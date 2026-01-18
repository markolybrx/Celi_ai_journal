// celi_ai v1.2.4 External Script
console.log("Script File Loaded");
document.getElementById('debug-status').innerText = "Script Running...";

const app = {
    data: { username: "Traveler", rank: "Observer", profile_pic: null },
    
    log: function(msg) {
        document.getElementById('debug-status').innerText = msg;
        console.log(msg);
    },

    // --- RENDER ---
    render: function() {
        const d = this.data;
        document.getElementById('greeting').innerText = `Hello, ${d.username || 'Traveler'}!`;
        document.getElementById('rank-display').innerText = d.rank || 'Observer';
        
        // Image Logic
        const defaultIcon = document.getElementById('icon-user').outerHTML;
        let imgHTML = defaultIcon;
        if (d.profile_pic && d.profile_pic.length > 50) {
            imgHTML = `<img src="${d.profile_pic}" class="profile-img" style="border-radius:12px; width:100%; height:100%; object-fit:cover;">`;
            let roundImg = `<img src="${d.profile_pic}" class="profile-img" style="border-radius:50%; width:100%; height:100%; object-fit:cover;">`;
            document.getElementById('portal-profile-container').innerHTML = roundImg;
        } else {
            document.getElementById('portal-profile-container').innerHTML = defaultIcon;
        }
        document.getElementById('header-profile-container').innerHTML = imgHTML;

        // Profile Data
        document.getElementById('profile-name').innerText = d.username;
        document.getElementById('profile-bday').innerText = d.birthday || '--';
        if(d.fav_color) document.getElementById('profile-color-dot').style.backgroundColor = d.fav_color;
        document.getElementById('celi-analysis-text').innerText = d.celi_analysis || "Connecting...";
        
        // Pre-fill Edit
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
            this.render(); // Render what we have
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
            reader.onload = (e) => {
                payload.profile_pic = e.target.result;
                send(payload);
            };
            reader.readAsDataURL(file);
        } else {
            send(payload);
        }
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
        } catch (e) {
            this.log("Msg Error");
        }
    }
};

// --- BOOTSTRAP ---
document.addEventListener('DOMContentLoaded', () => {
    app.sync();
    setInterval(() => app.sync(), 30000);
});
