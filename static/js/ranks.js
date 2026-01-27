// --- RANK CONFIGURATION ---
const PHASE_MAP = {
    "Observer": "Phase I: Awakening",
    "Moonwalker": "Phase I: Awakening",
    
    "Celestial": "Phase II: Ascension",
    "Stellar": "Phase II: Ascension",
    
    "Interstellar": "Phase III: Expansion",
    "Galactic": "Phase III: Expansion",
    
    "Intergalactic": "Phase IV: Transcendence",
    "Ethereal": "Phase IV: Transcendence"
};

// V11.4: Define Colors for the side-lines
const PHASE_COLORS = {
    "Phase I: Awakening": "#00f2fe",      // Cyan (Base Mood)
    "Phase II: Ascension": "#8b5cf6",     // Violet
    "Phase III: Expansion": "#ec4899",    // Pink/Magenta
    "Phase IV: Transcendence": "#f59e0b"  // Gold/Amber
};

const DEFAULT_PHASE = "Unknown Phase";

function openRanksModal() { 
    if (!globalRankTree) return; 
    
    const container = document.getElementById('ranks-list-container'); 
    container.innerHTML = ''; 
    container.className = 'tree-container'; 
    
    const modal = document.getElementById('ranks-modal'); 
    modal.style.display = 'flex'; 
    setTimeout(() => modal.classList.add('active'), 10); 
    
    // Header Population
    document.getElementById('modal-rank-icon').innerHTML = document.getElementById('main-rank-icon').innerHTML; 
    document.getElementById('modal-rank-name').innerText = document.getElementById('rank-display').innerText; 
    document.getElementById('modal-psyche-display').innerText = document.getElementById('rank-psyche').innerText;
    document.getElementById('modal-progress-bar').style.width = document.getElementById('rank-progress-bar').style.width; 
    document.getElementById('modal-sd-text').innerText = document.getElementById('stardust-cnt').innerText; 
    
    const normalize = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
    const currentTitleRaw = document.getElementById('rank-display').innerText;
    const currentTitleNorm = normalize(currentTitleRaw);
    const flatList = globalRankTree.ranks;
    const currentFlatIndex = flatList.findIndex(r => normalize(r.title) === currentTitleNorm);

    if(currentFlatIndex !== -1) {
        document.getElementById('modal-synth-text').innerText = flatList[currentFlatIndex].desc;
    } else {
        document.getElementById('modal-synth-text').innerText = flatList[0].desc;
    }

    // Grouping Logic
    const groupedRanks = {}; 
    const orderedKeys = [];

    flatList.forEach((rank, index) => {
        const mainName = rank.title.split(' ')[0]; 
        
        if (!groupedRanks[mainName]) {
            groupedRanks[mainName] = { 
                name: mainName, 
                subRanks: [], 
                isActiveGroup: false,
                icon: rank.svg,
                phase: PHASE_MAP[mainName] || DEFAULT_PHASE
            };
            orderedKeys.push(mainName);
        }
        
        const isCurrentNode = (index === currentFlatIndex);
        if (isCurrentNode) groupedRanks[mainName].isActiveGroup = true;

        groupedRanks[mainName].subRanks.push({
            ...rank,
            globalIndex: index,
            isCurrent: isCurrentNode,
            isUnlocked: index <= currentFlatIndex
        });
    });

    // Render Loop
    let lastRenderedPhase = "";

    orderedKeys.forEach(key => {
        const group = groupedRanks[key];
        
        // 1. Insert Phase Header with Dynamic Color
        if (group.phase !== lastRenderedPhase) {
            const phaseEl = document.createElement('div');
            phaseEl.className = 'phase-header';
            phaseEl.innerText = group.phase;
            
            // V11.4: Apply Color to Border
            const phaseColor = PHASE_COLORS[group.phase] || "var(--mood)";
            phaseEl.style.borderLeftColor = phaseColor;
            // Optional: Also tint the text slightly to match?
            // phaseEl.style.color = phaseColor; 
            
            container.appendChild(phaseEl);
            lastRenderedPhase = group.phase;
        }

        // 2. Render Accordion Group
        const groupEl = document.createElement('div');
        groupEl.className = `rank-group ${group.isActiveGroup ? 'open active' : ''}`;
        
        const isGroupUnlocked = group.subRanks[0].isUnlocked;
        const lockClass = isGroupUnlocked ? '' : 'locked';

        const header = document.createElement('div');
        header.className = `group-header ${lockClass}`;
        
        header.innerHTML = `
            <div class="group-label">
                <div class="group-left-icon">${group.icon}</div>
                <span class="group-title">${group.name}</span>
            </div>
            <div class="group-icon">${ICON_CHEVRON}</div>
        `;
        
        header.onclick = () => {
            document.querySelectorAll('.rank-group').forEach(el => { if (el !== groupEl) el.classList.remove('open'); });
            groupEl.classList.toggle('open');
            setTimeout(() => groupEl.scrollIntoView({behavior: 'smooth', block: 'center'}), 300);
        };
        groupEl.appendChild(header);

        const subList = document.createElement('div');
        subList.className = 'rank-sublist';

        group.subRanks.forEach(sub => {
            const node = document.createElement('div');
            node.className = `sub-node ${sub.isUnlocked ? 'unlocked' : ''} ${sub.isCurrent ? 'current' : ''}`;
            
            let status = sub.desc;
            if (sub.isCurrent) status = "Current Status";
            else if (!sub.isUnlocked) status = "Locked";

            node.innerHTML = `
                <div class="flex-1">
                    <div class="sub-title">${sub.title}</div>
                    <div class="sub-desc">${status}</div>
                </div>
                ${sub.isUnlocked ? '<div class="text-[var(--mood)]">✔</div>' : '<div class="opacity-30">🔒</div>'}
            `;
            subList.appendChild(node);
        });

        groupEl.appendChild(subList);
        container.appendChild(groupEl);
    });
    
    setTimeout(() => { 
        const active = container.querySelector('.rank-group.active'); 
        if(active) active.scrollIntoView({behavior: 'smooth', block: 'center'}); 
    }, 200); 
}
