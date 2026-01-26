async function loadData() { 
    try { 
        const res = await fetch('/api/data'); if(!res.ok) return; 
        const data = await res.json(); 
        if(data.status === 'guest') { window.location.href='/login'; return; } 
        
        globalRankTree = data.progression_tree; currentLockIcon = data.progression_tree.lock_icon; 
        document.getElementById('greeting-text').innerText = `Good Day, ${data.first_name}`; 
        document.getElementById('rank-display').innerText = data.rank; 
        document.getElementById('rank-psyche').innerText = data.rank_psyche; 
        document.getElementById('rank-progress-bar').style.width = `${data.rank_progress}%`; 
        document.getElementById('stardust-cnt').innerText = `${data.stardust_current}/${data.stardust_max} SD`; 
        document.getElementById('pfp-img').src = data.profile_pic || ''; 
        
        // --- RESTORED RANK COLORS ---
        // We use data.current_color (Rank Color) as the main theme (--mood)
        // This ensures buttons/progress bars match the Rank (Blue, Gold, etc.)
        document.documentElement.style.setProperty('--mood', data.current_color); 

        document.getElementById('main-rank-icon').innerHTML = data.current_svg; 
        document.getElementById('profile-pfp-large').src = data.profile_pic || ''; 
        document.getElementById('profile-fullname').innerText = `${data.first_name} ${data.last_name}`; 
        document.getElementById('profile-id').innerText = data.username; 
        document.getElementById('profile-color-text').innerText = data.aura_color; 
        
        // COLOR DOT LOGIC: 
        // Try to set bg to Aura Color. If it's a weird name, it might fail to render.
        // We fallback to Rank Color if needed visually, but CSS doesn't support fallback easily in inline styles.
        // So we just set it. If "Neon Blue" is invalid CSS, it shows transparent.
        // To fix this, we can force the rank color if the string doesn't look like a hex/rgb/standard color.
        const dot = document.getElementById('profile-color-dot');
        dot.style.backgroundColor = data.aura_color;
        // Simple check: if background is empty after setting (invalid color), set to rank color
        if (dot.style.backgroundColor === '') {
             dot.style.backgroundColor = data.current_color;
        }

        document.getElementById('profile-secret-q').innerText = SQ_MAP[data.secret_question] || data.secret_question;
        
        document.getElementById('edit-fname').value = data.first_name; 
        document.getElementById('edit-lname').value = data.last_name; 
        document.getElementById('edit-color').value = data.aura_color; 
        document.getElementById('edit-uid-display').innerText = data.username;
        document.getElementById('theme-btn').innerText = document.documentElement.getAttribute('data-theme') === 'light' ? 'Light' : 'Dark';
        
        if(data.history) fullChatHistory = data.history; 
        userHistoryDates = Object.values(data.history).map(e=>e.date); 
        renderCalendar(); 
    } catch(e) { console.error(e); } 
}
