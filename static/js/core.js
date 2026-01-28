// --- GLOBAL STATE ---
let isProcessing = false; 
let currentCalendarDate = new Date(); 
let fullChatHistory = {}; 
let userHistoryDates = []; 
let currentMode = 'journal'; 
let activeMediaFile = null; 
let activeAudioFile = null; 
let globalRankTree = null; 
let isGalaxyActive = false;

// --- UTILS ---
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    document.getElementById('theme-btn').innerText = next === 'light' ? 'Dark' : 'Light';
}
// Init Theme
if(localStorage.getItem('theme') === 'light') toggleTheme();
