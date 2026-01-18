// celi_ai v1.2.5 External Script
console.log("Script File Loaded v1.2.5");
document.getElementById('debug-status').innerText = "Core Active";

const PHASE_COLORS = { 
    "The Awakening Phase": "#00f2fe", // Cyan
    "The Ignition Phase": "#fbbf24",  // Gold
    "The Expansion Phase": "#8b5cf6", // Violet
    "The Singularity": "#ffffff"      // White
};

const app = {
    data: { username: "Traveler", rank: "Observer", profile_pic: null, rank_config: [] },
    
    log: function(msg) {
        document.getElementById('debug-status').innerText = msg;
        console.log(msg);
    },

    // --- RENDER ---
    render: function() {
        const d = this.data;
        const phaseColor = PHASE_COLORS[d.phase] || "#00f2fe";
        
        // 1. GLOBAL THEME
        document.documentElement.style.setProperty('--mood', phaseColor);
        document.getElementById('greeting').innerText = `Hello, ${d.username || 'Traveler'}!`;
        document.getElementById('rank-display').innerText = d.rank || 'Observer';
        document.getElementById('rank-display').style.color = phaseColor;
        document.getElementById('rank-bar').style.backgroundColor = phaseColor;
        document.getElementById('rank-bar').style.width = (d.rank_progress || 0) + '%';
        document.getElementById('mini-rank-logo').style.borderColor = phaseColor;
        document.getElementById('mini-rank-logo').style.boxShadow = `0 0 10px ${phaseColor}66`;

        // 2. PORTAL GEOMETRY
        const largeIcon = document.getElementById('portal-rank-icon');
        largeIcon.style.borderColor = phaseColor;
        largeIcon.style.boxShadow = `0 0 30px ${phaseColor}44`;
        
        // Logic: Observer = Pulsing Circle | Others = Diamond
        if (d.rank && d.rank.includes("Observer")) {
            largeIcon.innerHTML = `<div class="w-16 h-16 bg-white rounded-full pulse-glow" style="color:${phaseColor}"></div>`;
        } else {
            largeIcon.innerHTML = `<div class="w-16 h-16 border-4 border-current rotate-45 shadow-[0_0_20px_currentColor]" style="color:${phaseColor}"></div>`;
        }

        // 3. STARS
        const roman = (d.rank_roman || "I");
        const count = {"I":1, "II":2, "III":3, "IV":4, "V":5}[roman] || 1;
        document.getElementById('portal-level-stars').innerHTML = Array(count).fill(`<div class="star-four-point" style="color:${phaseColor}"></div>`).join('');
        
        // 4. PORTAL TEXT
        document.getElementById('portal-rank-name').innerText = d.rank;
        document.getElementById('portal-rank-name').style.color = phaseColor;
        document.getElementById('portal-progress-bar').style.backgroundColor = phaseColor;
        document.getElementById('portal-progress-bar').style.width = (d.rank_progress || 0) + '%';
        document.getElementById('portal-points').innerText = `${d.points || 0} Stars`;
        document.getElementById('portal-synthesis-text').innerText = d.rank_synthesis || "Connecting...";

        // 5. THE LIST (Restored Logic)
        const listContainer = document.getElementById('portal-future-list');
        if (d.rank_config && d.rank_config.length > 0) {
            let currentPhaseName = "";
            let html = "";
            
            d.rank_config.forEach(r => {
                const pColor = PHASE_COLORS[r.phase];
                
                // New Phase Header
                if (r.phase !== currentPhaseName) {
                    currentPhaseName = r.phase;
                    html += `
                        <div class="mt-6 mb-2 pl-2 border-l-2 text-[9px] font-black uppercase tracking-widest" 
                             style="color:${pColor}; border-color:${pColor}44; text-shadow: 0 0 10px ${pColor}44;">
                            ${currentPhaseName}
                        </div>`;
                }
                
                // Rank Item
                const isUnlocked = (d.points || 0) >= r.threshold;
                // Highlight logic: Bright color for header, dimmer opacity for item text
                const itemColor = isUnlocked ? pColor : "rgba(255,255,255,0.3)";
                
                html += `
                    <div class="flex justify-between items-center py-2 px-2 border-b border-white/5">
                        <span class="text-[10px] font-bold uppercase" style="color:${itemColor}">${r.name}</span>
                        <span class="text-[8px] uppercase opacity-40">${isUnlocked ? 'ALIGNED' : `${r.threshold - (d.points || 0)} to go`}</span>
                    </div>`;
            });
            listContainer.innerHTML = html;
        }

        // 6. PROFILE & IMAGES
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
        
        // Edit Inputs
        document.getElementById('edit-bday').value = (d.birthday && d.birthday !== 'Unset') ? d.birthday : '';
        document.getElementById('edit-color').value = d.fav_color || '#00f2fe';
    },

    // --- SYNC ---
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

    // --- ACTIONS ---
    openTab: function(id) {
        document.querySelectorAll('.overlay').forEach(el => el.style.display = 'none');
        const target = document.getElementById(id + '-overlay');
        if (target) target.style.display = 'flex';
        this.sync();
    },

    closeUI: function() {
        document.querySelectorAll('.overlay, #intent-modal').forEach(el => el.style.display = 'none');
    },

    showIntent: function() {
        document.getElementById('intent-modal').style.display = 'flex';
    },

    openEditProfile: function() {
        document.getElementById('edit-modal').style.display = 'flex';
    },

    startChat: function(mode) {
        this.currentMode = mode;
        this.closeUI();
        document.getElementById('chat-overlay').style.display = 'flex';
    },

    saveProfile: async function() {
        const bday = document.getElementById('edit-bday').value;
        const color = document.getElementById('edit-color').value;
        const file = document.getElementById('edit-pic').files[0];
        let payload = { birthday: bday, fav_color: color };
        
        const send = async (p) => {
            this.log("Saving...");
            await fetch('/api/update_profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(p)
            });
            document.getElementById('edit-modal').style.display = 'none';
            this.sync();
        };

        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => { payload.profile_pic = e.target.result; send(payload); };
            reader.readAsDataURL(file);
        } else { send(payload); }
    },

    confirmDelete: async function() {
        if (confirm("Permanently delete data?")) {
            await fetch('/api/delete_user', { method: 'POST' });
            window.location.reload();
        }
    },

    sendAction: async function() {
        const input = document.getElementById('msg-input');
        const text = input.value;
        if (!text) return;
        
        const con = document.getElementById('msg-container');
        con.innerHTML += `<div class="p-2 bg-white/10 rounded mb-2 text-right">${text}</div>`;
        input.value = '';
        
        try {
            const res = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, mode: this.currentMode || 'journal' })
            });
            const d = await res.json();
            con.innerHTML += `<div class="p-2 text-cyan-400 mb-2 text-left">${d.reply}</div>`;
            this.sync();
        } catch (e) { this.log("Msg Error"); }
    }
};

document.addEventListener('DOMContentLoaded', () => { app.sync(); setInterval(() => app.sync(), 30000); });
