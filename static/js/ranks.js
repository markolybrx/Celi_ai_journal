function openRanksModal() { 
    const modal = document.getElementById('ranks-modal');
    modal.classList.add('active');
    renderRankTree();
}
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

function renderRankTree() {
    const container = document.getElementById('ranks-list-container');
    container.innerHTML = '';
    
    // Group logic based on phases (simplified)
    const phases = { "Phase I": [], "Phase II": [], "Phase III": [] };
    
    globalRankTree.forEach(rank => {
        if(rank.title.includes("Observer") || rank.title.includes("Moonwalker")) phases["Phase I"].push(rank);
        else if(rank.title.includes("Celestial") || rank.title.includes("Stellar")) phases["Phase II"].push(rank);
        else phases["Phase III"].push(rank);
    });

    Object.keys(phases).forEach(phaseName => {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'rank-group';
        groupDiv.innerHTML = `<div class="p-3 font-bold uppercase tracking-widest text-xs opacity-50">${phaseName}</div>`;
        
        phases[phaseName].forEach(r => {
            const node = document.createElement('div');
            // Logic to determine if locked/unlocked based on current user rank index would go here
            // For anchor v1.0.0, we just list them
            node.className = 'p-3 border-t border-[var(--border)] flex justify-between items-center';
            node.innerHTML = `<span>${r.title}</span> <span class="text-[10px] opacity-50">${r.req} SD</span>`;
            groupDiv.appendChild(node);
        });
        container.appendChild(groupDiv);
    });
}
