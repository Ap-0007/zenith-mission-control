// --- AETHER ENGINE: UI & UTILS ---
function logOrch(type, msg) {
    const log = document.getElementById('orch-log');
    const time = new Date().toLocaleTimeString().split(' ')[0];
    log.innerHTML = `<div><span style="color:var(--accent-primary)">[${time}]</span> [${type}] ${msg}</div>` + log.innerHTML;
}

// --- 3D TILT LOGIC ---
function apply3DTilt(card) {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = (y - centerY) / 30;
        const rotateY = (centerX - x) / 30;
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.01, 1.01, 1.01)`;
    });

    card.addEventListener('mouseleave', () => {
        card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
    });
}

// --- SENSORY HUD: PULSE ENGINE ---
async function fetchHUD() {
    const list = document.getElementById('pulse-grid');
    if (!window.projects) return;
    
    list.innerHTML = window.projects.map(p => `
        <div class="pulse-node ${p.health}" 
             onclick="launch('${p.path}', 'vscode')"
             title="${p.name.toUpperCase()} // STATUS: ${p.health.toUpperCase()}">
        </div>
    `).join('');
}

// --- ORCHESTRA AUTOMATION ---
async function runOrchestra(action) {
    const progCont = document.getElementById('orch-progress-container');
    const progBar = document.getElementById('orch-progress-bar');
    
    logOrch('PROC', `Initializing ${action.toUpperCase()} protocol...`);
    progCont.style.display = 'block';
    progBar.style.width = '30%'; // Initial kick
    
    try {
        const response = await fetch('/api/automate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ action })
        });
        progBar.style.width = '80%';
        const data = await response.json();
        progBar.style.width = '100%';
        setTimeout(() => { progCont.style.display = 'none'; progBar.style.width = '0%'; }, 1000);
        logOrch('DONE', data.message);
    } catch (e) {
        progCont.style.display = 'none';
        logOrch('ERR ', e.message);
    }
}

// --- WORKSPACE DNA ---
async function fetchStats() {
    try {
        const response = await fetch('/api/workspace_stats');
        const data = await response.json();
        
        document.getElementById('stat-projects').innerText = data.project_count;
        document.getElementById('stat-disk').innerText = data.disk_root + '%';
        
        const container = document.getElementById('dna-container');
        container.innerHTML = '';
        
        const colors = ['var(--accent-primary)', 'var(--accent-secondary)', 'var(--accent-tri)', '#fff'];
        let idx = 0;
        for (const [lang, count] of Object.entries(data.dna)) {
            const row = document.createElement('div');
            row.style.marginBottom = '8px';
            row.innerHTML = `
                <div style="display:flex; justify-content:space-between; font-size:0.55rem; font-weight:800; margin-bottom:2px; color:var(--text-muted);">
                    <span>${lang.toUpperCase()}</span>
                </div>
                <div class="dna-bar">
                    <div class="dna-fill" style="width:${Math.min((count / data.dna_total) * 100, 100)}%; background:${colors[idx % 4]}"></div>
                </div>
            `;
            container.appendChild(row);
            idx++;
        }
    } catch (e) {}
}

// --- PROJECT GRID (3D) ---
async function fetchProjects() {
    try {
        const r = await fetch('/api/projects');
        const projects = await r.json();
        window.projects = projects; // Cache for HUD
        const list = document.getElementById('project-list');
        list.innerHTML = '';
        
        projects.forEach(p => {
            const card = document.createElement('div');
            card.className = 'project-card';
            card.innerHTML = `
                <div class="project-inner">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="project-name" style="font-size:1rem; font-weight:700; opacity:0.9;">${p.name.toUpperCase()}</div>
                        <div class="pulse-node ${p.health}" style="width:8px; height:8px;"></div>
                    </div>
                    
                    <div class="project-meta">
                        <div style="display:flex; gap:8px;">
                            <span class="badge git" style="color:var(--accent-primary); font-size:0.55rem;">${p.git.branch}</span>
                            <span class="badge" style="background:rgba(255,255,255,0.03); font-size:0.55rem;">${p.last_mod.split(' ')[2]} ${p.last_mod.split(' ')[1]}</span>
                        </div>
                    </div>

                    </div>
                </div>
            `;
            apply3DTilt(card);
            list.appendChild(card);
        });
    } catch (e) {}
}

// --- SEARCH & SYSTEM ---
const sInput = document.getElementById('universal-search');
const sRes = document.getElementById('search-results');
sInput.oninput = async (e) => {
    const q = e.target.value;
    if(q.length < 3) { sRes.style.display = 'none'; return; }
    const r = await fetch('/api/search?q=' + q);
    const data = await r.json();
    sRes.innerHTML = data.map(i => `
        <div class="search-item" onclick="launch('${i.file}', 'vscode', '${i.line}')">
            <div style="font-weight:800; font-size:0.8rem; color:var(--accent-primary)">${i.file.split('/').slice(-2).join('/')}:${i.line}</div>
            <div style="font-size:0.75rem; opacity:0.6; font-family:'JetBrains Mono'">${i.content}</div>
        </div>
    `).join('');
    sRes.style.display = 'block';
};

async function launch(path, target, line = '') {
    const r = await fetch('/api/launch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({path, target, line})
    });
}

async function fetchMetrics() {
    const r = await fetch('/api/metrics');
    const d = await r.json();
    document.getElementById('cpu-val').innerText = d.cpu + '%';
    document.getElementById('mem-val').innerText = d.mem + '%';
    document.getElementById('system-time').innerText = new Date().toLocaleTimeString();
}

async function fetchTodos() {
    const r = await fetch('/api/todos');
    const data = await r.json();
    document.getElementById('todo-list').innerHTML = data.map(t => `
        <div style="margin-bottom:12px; padding:10px; background:rgba(255,255,255,0.02); border-left:2px solid var(--accent-secondary)">
            <div style="font-size:0.6rem; color:var(--accent-secondary); font-weight:800">${t.project}</div>
            <div style="opacity:0.8">${t.text}</div>
        </div>
    `).join('');
}

// Parallax Background
document.addEventListener('mousemove', (e) => {
    const bg = document.querySelector('.aether-bg');
    if (!bg) return;
    const x = (e.clientX / window.innerWidth - 0.5) * 8;
    const y = (e.clientY / window.innerHeight - 0.5) * 8;
    bg.style.transform = `translate(${x}px, ${y}px)`;
});

// Initialization
fetchProjects().then(() => fetchHUD());
fetchStats();
fetchTodos();

// Removed Kinetic Timeline Scroll (Header Replaced)

setInterval(fetchMetrics, 2000);
setInterval(() => fetchProjects().then(() => fetchHUD()), 10000); // Pulse refresh
document.onkeydown = (e) => { if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); sInput.focus(); } };
window.onclick = (e) => { if (e.target != sInput) sRes.style.display = 'none'; };
logOrch('SYST', 'AETHER protocols active. Workspace intelligence synchronized.');
