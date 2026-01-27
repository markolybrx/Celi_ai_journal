function openRanksModal() { 
    if (!globalRankTree) return; 
    
    const container = document.getElementById('ranks-list-container'); 
    container.innerHTML = ''; 
    container.className = 'tree-container'; 
    
    const modal = document.getElementById('ranks-modal'); 
    modal.style.display = 'flex'; 
    setTimeout(() => modal.classList.add('active'), 10); 
    
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

    const groupedRanks = {};
    flatList.forEach((rank, index) => {
        const mainName = rank.title.split(' ')[0]; 
        if (!groupedRanks[mainName]) {
            groupedRanks[mainName] = { 
                name: mainName, 
                subRanks: [], 
                isActiveGroup: false,
                icon: rank.svg 
            };
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

    Object.values(groupedRanks).forEach(group => {
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
