/* ═══════════════════════════════════════════
   IMED PREDICTOR — app_v411_final.js
   Version: 4.12.0 (TOTAL INTEGRATION)
   Features: Real-time Sync, Integrated IVN, GPS Upload, Trends
   ════════════════════════════════════════════ */

const THRESH = { iriCritical: 60, lapses: 2, iriOptimal: 85 };

let db, auth;
let unsubscribe = null;
let allPerformance = [];
let gAthletesCache = [];
let correlationChart = null;
let reportCharts = [];
let selectedGpsBrand = 'auto';
let selectedFile = null;
let gActiveProfileId = null;

// ─── Initialization ───
const firebaseConfig = {
  apiKey:            "AIzaSyA-eVf8UncVMgN6mDgsgjqbj2hhPmRDjUs",
  authDomain:        "app-imed-sport.firebaseapp.com",
  projectId:         "app-imed-sport",
  storageBucket:     "app-imed-sport.firebasestorage.app",
  messagingSenderId: "300860465249",
  appId:             "1:300860465249:web:08f49c42e30a7bab42ca20"
};

try {
    if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
    db = firebase.firestore();
    auth = firebase.auth();
    init();
} catch (e) { console.error("Firebase Init Error:", e); }

async function init() {
    showView('dashboard');
    startRealtimeListener();
    startAthletesOnboarding();
    initGpsBrandSelector();
}

// ─── Onboarding & Real-time ───
function startAthletesOnboarding() {
    db.collection('athletes').onSnapshot(snap => {
        gAthletesCache = snap.docs.map(d => {
            const data = d.data();
            return { id: d.id, ...data, fullName: data.fullName || `${data.firstName || ''} ${data.lastName || ''}`.trim() || d.id };
        });
        renderAthletesTable();
        renderSncTable();
        renderDashboard();
        populateAthleteSelects();
    });
}

function startRealtimeListener() {
    if (unsubscribe) unsubscribe();
    unsubscribe = db.collection('Daily_Performance')
        .orderBy('timestamp', 'desc')
        .limit(100)
        .onSnapshot(snap => {
            allPerformance = snap.docs.map(d => ({ id: d.id, ...d.data() }));
            renderDashboard();
            renderSncTable();
            renderAthletesTable();
        });
}

// ─── Navigation ───
function showView(viewId) {
    const view = document.getElementById('view-' + viewId);
    const nav = document.getElementById('nav-' + viewId);
    if (!view) return;

    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    view.classList.add('active');
    
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    if (nav) nav.classList.add('active');
    
    const titleMap = { 
        'dashboard': 'Dashboard de Predicción', 
        'snc': 'Monitoreo SNC Diario', 
        'athletes': 'Gestión de Atletas', 
        'reports': 'Análisis de Tendencias', 
        'upload': 'Carga de Datos GPS',
        'settings': 'Configuración del Sistema'
    };
    const titleEl = document.getElementById('page-title');
    if (titleEl) titleEl.textContent = titleMap[viewId] || 'IMED Predictor';
    if (viewId === 'reports') loadAthleteReport(document.getElementById('report-athlete-select')?.value);
}

// ─── Engines ───
function calculateWellness(p) {
    const w = p.wellness || {};
    const h = w.sleepHours ?? p.sleep_hours ?? 7;
    const q = w.sleepQuality ?? p.sleep_quality ?? 3;
    const s = w.stressLevel ?? p.stress ?? 2;
    const f = w.fatigueLevel ?? p.fatigue ?? 2;

    const hScore = (Math.min(8, h) / 8) * 40;
    const qScore = (q / 5) * 20;
    const sScore = ((6 - s) / 5) * 20;
    const fScore = ((6 - f) / 5) * 20;
    return Math.round(hScore + qScore + sScore + fScore);
}

function getUnifiedStatus(p) {
    const iri = p.iri ?? 75;
    const metrics = p.pvt?.metrics || {};
    const lapses = metrics.lapses ?? p.lapses ?? 0;
    const wellness = calculateWellness(p);
    
    const naBase = (iri * 0.6) + (wellness * 0.4);
    const na = Math.max(0, naBase * (1 - (lapses * 0.1)));
    
    const gps = p.gps || {};
    const decel = gps.decel_high || gps.decel_z5 || 0;
    const sprint = (gps.sprint_dist || gps.sprint_distance || 0) / 100;
    const load = (decel * 0.7) + (sprint * 0.3);
    const ivn = na > 0 ? (load / (na / 100)) : load;

    let level = 'GREEN', label = 'ÓPTIMO';
    if (na < 55 || lapses > 2 || ivn > 15) { level = 'RED'; label = 'RIESGO CRÍTICO'; }
    else if (na < 80 || ivn > 8) { level = 'YELLOW'; label = 'ADVERTENCIA'; }

    return { 
        level, label, na, wellness, ivn,
        badgeClass: `badge-${level.toLowerCase()}`, 
        ringClass: `ring-${level.toLowerCase()}` 
    };
}

function calcSNC(p) { return getUnifiedStatus(p); }
function calcIVN(p) { return getUnifiedStatus(p); }

// ─── Rendering ───
function renderDashboard() {
    const container = document.getElementById('athlete-list');
    if (!container) return;
    const today = new Date().toISOString().split('T')[0];
    const latest = {};
    
    allPerformance.forEach(p => { 
        const aid = String(p.athleteId || "").trim();
        if (aid && !latest[aid]) latest[aid] = p;
    });
    
    const latestList = Object.values(latest);
    let counts = { RED: 0, YELLOW: 0, GREEN: 0 };
    
    container.innerHTML = latestList.length ? latestList.map(p => {
        const ivn = calcIVN(p);
        if (p.date === today) counts[ivn.level]++;
        const initials = (p.athleteName || 'AT').split(' ').map(w => w[0]).join('').slice(0, 2);
        return `
            <div class="athlete-card" onclick="openSncModal('${p.athleteId}')">
                <div class="athlete-avatar">${initials}<div class="risk-ring ${ivn.ringClass}"></div></div>
                <div class="athlete-info">
                    <div class="athlete-name">${p.athleteName || p.athleteId}</div>
                    <div class="athlete-pos">${p.position || '—'}</div>
                </div>
                <div class="athlete-metrics">
                    <div class="metric-mini"><div class="val">${Math.round(p.iri)}</div><div class="lbl">IRI</div></div>
                    <div class="metric-mini"><div class="val">${p.pvt?.metrics?.lapses ?? p.lapses ?? 0}</div><div class="lbl">LAPSES</div></div>
                </div>
                <span class="risk-badge ${ivn.badgeClass}">${ivn.label}</span>
            </div>`;
    }).join('') : '<div class="empty-state">No hay evaluaciones registradas hoy.</div>';
    
    document.getElementById('count-critical').textContent = counts.RED;
    document.getElementById('count-warning').textContent = counts.YELLOW;
    document.getElementById('count-optimal').textContent = counts.GREEN;
    
    document.getElementById('kpi-critical').textContent = counts.RED;
    document.getElementById('kpi-coordination').textContent = counts.YELLOW;
    document.getElementById('kpi-optimal').textContent = counts.GREEN;
    document.getElementById('kpi-total').textContent = latestList.filter(x => x.date === today).length;

    updateChart();
}

function updateChart() {
    const ctx = document.getElementById('correlationChart');
    if (!ctx) return;
    const days = parseInt(document.getElementById('chart-filter')?.value || 7);
    const cutoff = new Date(); cutoff.setDate(cutoff.getDate() - days);
    
    const data = allPerformance
        .filter(p => new Date(p.date) >= cutoff)
        .map(p => {
            const ivn = calcIVN(p);
            return {
                x: Math.round(p.iri),
                y: p.gps?.decel_high || p.gps?.decel_z5 || 0,
                r: 6,
                color: ivn.level === 'RED' ? '#FF4D4D' : (ivn.level === 'YELLOW' ? '#FFD60A' : '#32D74B')
            };
        });

    if (correlationChart) correlationChart.destroy();
    correlationChart = new Chart(ctx, {
        type: 'bubble',
        data: { datasets: [{ label: 'Atletas', data: data, backgroundColor: data.map(d => d.color) }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { title: { display: true, text: 'Índice IRI (SNC)', color: '#636375' }, grid: { color: 'rgba(255,255,255,0.05)' }, min: 0, max: 100 },
                y: { title: { display: true, text: 'Desaceleraciones Z5', color: '#636375' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

function renderSncTable() {
    const list = document.getElementById('snc-athletes-list');
    if (!list) return;
    const today = new Date().toISOString().split('T')[0];
    
    list.innerHTML = gAthletesCache.map(a => {
        const p = allPerformance.find(x => String(x.athleteId).trim() === String(a.id).trim());
        const snc = p ? calcSNC(p) : { level: 'GRAY', label: 'PENDIENTE', badgeClass: 'badge-gray' };
        const isDone = p?.date === today;
        return `
            <tr onclick="openSncModal('${a.id}')">
                <td><strong>${a.fullName}</strong></td>
                <td><span class="badge badge-gray">${a.team || 'SNC'}</span></td>
                <td>${p ? Math.round(p.iri) : '—'}</td>
                <td><span class="risk-badge ${snc.badgeClass}">${snc.label}</span></td>
                <td>NORMAL</td>
                <td><span class="risk-badge badge-green">ESTABLE</span></td>
                <td>${p ? p.date : '—'}</td>
                <td>${p?.timestamp ? (p.timestamp.seconds ? new Date(p.timestamp.seconds*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}) : '—') : '—'}</td>
                <td><span class="risk-badge ${isDone ? 'badge-green' : 'badge-gray'}">${isDone ? 'SI' : 'NO'}</span></td>
                <td><button class="btn-mini">Análisis</button></td>
                <td><button class="btn-delete" onclick="event.stopPropagation(); deleteAthlete('${a.id}')">🗑</button></td>
            </tr>`;
    }).join('');
}

function renderAthletesTable(f = '') {
    const list = document.getElementById('athletes-table-list');
    if (!list) return;
    list.innerHTML = gAthletesCache.filter(a => a.fullName.toLowerCase().includes(f.toLowerCase())).map(a => `
        <tr onclick="openAthleteProfile('${a.id}')">
            <td><strong>${a.fullName}</strong></td>
            <td><span class="badge badge-gray">${a.team || 'General'}</span></td>
            <td>${a.position || '—'}</td>
            <td>${a.birthdate || '—'}</td>
            <td><button class="btn-mini" onclick="event.stopPropagation(); openAthleteProfile('${a.id}')">Ficha</button></td>
            <td><button class="btn-delete" onclick="event.stopPropagation(); deleteAthlete('${a.id}')">🗑</button></td>
        </tr>`).join('');
}

function filterAthletes(v) { renderAthletesTable(v); }

// ─── Modals ───
function openAthleteProfile(id) {
    gActiveProfileId = id;
    const a = gAthletesCache.find(x => x.id === id);
    if (!a) return;
    document.getElementById('prof-static-name').textContent = a.fullName;
    document.getElementById('prof-static-pos').textContent = a.position || '—';
    document.getElementById('tab-container-ficha').innerHTML = `
        <div class="grid-2col" style="margin-top:20px">
            <div class="panel glass"><div class="panel-label">EQUIPO</div><div class="panel-title">${a.team || '—'}</div></div>
            <div class="panel glass"><div class="panel-label">ESTADO</div><div class="panel-title">ACTIVO</div></div>
        </div>
        <div class="panel glass" style="margin-top:20px"><div class="panel-label">NOTAS</div><p>${a.notes || 'Sin observaciones.'}</p></div>`;
    document.getElementById('athlete-profile-modal').classList.remove('hidden');
}

function openSncModal(id) {
    const a = gAthletesCache.find(x => x.id === id);
    const p = allPerformance.find(x => String(x.athleteId).trim() === String(id).trim());
    if (!a || !p) return;
    
    const snc = calcSNC(p);
    const wellness = calculateWellness(p);
    const pvt = p.pvt?.metrics || {};

    document.getElementById('snc-modal-content').innerHTML = `
        <div class="modal-header">
            <div>
                <div class="panel-label">ANÁLISIS NEURO-RENDIMIENTO SNC</div>
                <h2 class="panel-title">${a.fullName}</h2>
                <div style="display:flex; gap:10px; align-items:center; margin-top:8px">
                    <span class="risk-badge ${snc.badgeClass}">${snc.label}</span>
                    <span style="font-size:11px; color:var(--text-3)">${p.date}</span>
                </div>
            </div>
            <button class="modal-close" onclick="closeSncModal()">✕</button>
        </div>
        <div class="modal-grid-stats">
            <div class="stat-card-mini active-iri"><div class="val">${Math.round(p.iri)}</div><div class="lbl">IRI SCORE</div></div>
            <div class="stat-card-mini"><div class="val">${pvt.lapses ?? p.lapses ?? 0}</div><div class="lbl">LAPSES</div></div>
            <div class="stat-card-mini"><div class="val">${pvt.meanLatency ?? p.avg_reaction ?? 280}</div><div class="lbl">LAT. MEDIA ms</div></div>
            <div class="stat-card-mini"><div class="val ${wellness < 60 ? 'text-red' : ''}">${wellness}</div><div class="lbl">WELLNESS /100</div></div>
        </div>
        <div class="detail-sections">
            <div class="detail-box">
                <div class="detail-box-header">🧠 PRUEBA PVT — RESULTADOS</div>
                ${renderDetailRow('Tiempo Más Rápido', pvt.fastest ?? p.best_reaction ?? 220, 'ms', 400, '#32D74B')}
                ${renderDetailRow('Latencia Media', pvt.meanLatency ?? p.avg_reaction ?? 280, 'ms', 400, '#32D74B')}
                ${renderDetailRow('Tiempo Más Lento', pvt.slowest ?? p.worst_reaction ?? 350, 'ms', 500, '#FFD60A')}
                ${renderDetailRow('Lapsos de Atención', pvt.lapses ?? p.lapses ?? 0, '/ 10 ensayos', 10, '#FF4D4D')}
            </div>
            <div class="detail-box">
                <div class="detail-box-header">💤 WELLNESS — ESTADO SUBJETIVO</div>
                ${renderDetailRow('Horas de Sueño', p.wellness?.sleepHours ?? p.sleep_hours ?? 7, 'h', 10, '#32D74B')}
                ${renderDetailRow('Calidad de Sueño', p.wellness?.sleepQuality ?? p.sleep_quality ?? 3, '/5', 5, '#FFD60A')}
                ${renderDetailRow('Nivel de Estrés', p.wellness?.stressLevel ?? p.stress ?? 2, '/5', 5, '#FF4D4D')}
                ${renderDetailRow('Fatiga Percibida', p.wellness?.fatigueLevel ?? p.fatigue ?? 2, '/5', 5, '#FFD60A')}
            </div>
        </div>
        <div class="prescription-box">
            <div class="prescription-title">⚡ DIAGNÓSTICO INTEGRADO NA-GPS — PRESCRIPCIÓN</div>
            <div class="prescription-text">
                <strong>Estado: ${snc.label}.</strong> Disponibilidad Neural Integrada: <strong>${Math.round(snc.na)}%</strong>. 
                El algoritmo ha detectado una correlación entre ${snc.wellness < 70 ? 'un Wellness pobre' : 'fatiga neural'} 
                y una carga mecánica de <strong>${snc.ivn.toFixed(1)}x</strong>.
                <br><br>
                <strong>Prescripción:</strong> ${snc.level === 'GREEN' ? 'Mantener cargas. Atleta en zona de adaptación.' : (snc.level === 'YELLOW' ? 'Moderar intensidad mecánica. Evitar sprints máximos.' : 'REDUCCIÓN INMEDIATA. Riesgo de lesión elevado por baja disponibilidad neural.')}
            </div>
            <button class="btn-primary w-full" style="margin-top:16px; background:var(--blue-dim); color:var(--blue); border:1px solid var(--blue)" onclick="viewAthleteTrends('${a.id}')">📊 Ver Tendencias Biométricas</button>
        </div>`;
    document.getElementById('snc-modal').classList.remove('hidden');
}

function viewAthleteTrends(id) {
    closeSncModal();
    showView('reports');
    const select = document.getElementById('report-athlete-select');
    if (select) {
        select.value = id;
        loadAthleteReport(id);
    }
}

function renderDetailRow(label, val, unit, max, color) {
    const perc = Math.min((val / max) * 100, 100);
    return `<div class="detail-row"><div class="detail-label">${label}</div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width:${perc}%; background:${color}"></div></div><div class="detail-value" style="color:${color}">${val}${unit}</div></div>`;
}

function closeSncModal() { document.getElementById('snc-modal').classList.add('hidden'); }
function closeAthleteProfile() { document.getElementById('athlete-profile-modal').classList.add('hidden'); }

// ─── Trends & Reports ───
function loadAthleteReport(athleteId) {
    const container = document.getElementById('report-container');
    const advancedContainer = document.getElementById('advanced-report-container');
    if (!athleteId) { 
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">📊</div><p>Selecciona un atleta</p></div>'; 
        advancedContainer.innerHTML = '';
        return; 
    }
    const records = allPerformance.filter(p => String(p.athleteId).trim() === String(athleteId).trim()).slice(0, 14).reverse();
    if (!records.length) { 
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">📭</div><p>Sin registros vinculados</p></div>'; 
        advancedContainer.innerHTML = '';
        return; 
    }

    reportCharts.forEach(c => c.destroy());
    reportCharts = [];

    const labels = records.map(p => p.date || '');
    const iriVals = records.map(p => p.iri || 0);
    const latencyVals = records.map(p => p.pvt?.metrics?.meanLatency ?? p.avg_reaction ?? 0);
    const sleepVals = records.map(p => p.wellness?.sleepHours ?? p.sleep_hours ?? 0);
    const stressVals = records.map(p => p.wellness?.stressLevel ?? p.stress ?? 0);

    container.innerHTML = `
        <div class="report-grid">
            ${renderReportCard('EVOLUCIÓN IRI (SNC)', 'chart-iri')}
            ${renderReportCard('LATENCIA SNC (MS)', 'chart-latency')}
            ${renderReportCard('CORRELACIÓN: IRI VS DESACELERACIONES', 'chart-corr')}
            ${renderReportCard('HORAS SUEÑO', 'chart-sleep')}
            ${renderReportCard('ESTRÉS', 'chart-stress')}
        </div>`;
    advancedContainer.innerHTML = '';

    createMiniChart('chart-iri', labels, iriVals, '#BF5AF2', 0, 100);
    createMiniChart('chart-latency', labels, latencyVals, '#00E5FF', 200, 450);
    createMiniChart('chart-sleep', labels, sleepVals, '#32D74B', 4, 12);
    createMiniChart('chart-stress', labels, stressVals, '#FFD60A', 1, 5);

    // Correlation Scatter
    const corrData = records.map(p => ({ x: p.gps?.decel_high || p.gps?.decel_z5 || 0, y: p.iri || 0 }));
    reportCharts.push(new Chart(document.getElementById('chart-corr'), {
        type: 'scatter',
        data: { datasets: [{ data: corrData, backgroundColor: '#BF5AF2', pointRadius: 7 }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { title: { display: true, text: 'DESACELERACIONES', color: '#636375', font: { size: 8, weight: '800' } }, grid: { color: 'rgba(255,255,255,0.03)' } },
                y: { min: 0, max: 100, title: { display: true, text: 'INDICE IRI', color: '#636375', font: { size: 8, weight: '800' } }, grid: { color: 'rgba(255,255,255,0.03)' } }
            }
        }
    }));
}

function createMiniChart(id, labels, data, color, min, max) {
    reportCharts.push(new Chart(document.getElementById(id), {
        type: 'line',
        data: { labels, datasets: [{ data, borderColor: color, backgroundColor: 'transparent', tension: 0.4, borderWidth: 3, pointRadius: 5, pointBackgroundColor: '#0a0c0f', pointBorderColor: color, pointBorderWidth: 2 }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { 
                legend: { display: false },
                datalabels: {
                    align: 'top', backgroundColor: color, borderRadius: 4, color: 'white', font: { weight: 'bold', size: 10 },
                    formatter: Math.round, padding: 4, offset: 8
                }
            },
            scales: {
                x: { display: true, grid: { display: false }, ticks: { color: '#636375', font: { size: 9 } } },
                y: { display: true, min: min, max: max, grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false }, ticks: { color: '#636375', font: { size: 9 }, stepSize: (max-min)/2 } }
            }
        }
    }));
}

function renderReportCard(title, canvasId) {
    return `<div class="report-card"><div class="report-card-title">${title}</div><div class="mini-chart-container"><canvas id="${canvasId}"></canvas></div></div>`;
}

// ─── GPS Upload Logic ───
function initGpsBrandSelector() {
    const container = document.getElementById('gps-brand-selector');
    if (!container || typeof GPS_BRANDS_DB === 'undefined') return;
    container.innerHTML = Object.values(GPS_BRANDS_DB).map(brand => `
        <div class="gps-brand-card ${brand.id === selectedGpsBrand ? 'selected' : ''}" id="brand-${brand.id}" onclick="selectGpsBrand('${brand.id}')">
            <div class="brand-logo" style="background: ${brand.color}22; border-color: ${brand.color}44"><span class="brand-emoji">${brand.logo}</span></div>
            <div class="brand-name">${brand.name}</div>
        </div>`).join('');
}

function selectGpsBrand(id) {
    selectedGpsBrand = id;
    document.querySelectorAll('.gps-brand-card').forEach(el => el.classList.remove('selected'));
    document.getElementById('brand-' + id)?.classList.add('selected');
}

function handleDragOver(e) { e.preventDefault(); document.getElementById('dropzone').classList.add('drag-over'); }
function handleDragLeave() { document.getElementById('dropzone').classList.remove('drag-over'); }
function handleDrop(e) { e.preventDefault(); document.getElementById('dropzone').classList.remove('drag-over'); if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]); }
function handleFileSelect(e) { if (e.target.files[0]) setFile(e.target.files[0]); }
function setFile(file) {
    selectedFile = file;
    document.getElementById('dropzone-filename').textContent = `✓ ${file.name}`;
    document.getElementById('btn-process').disabled = false;
}

async function processCSV() {
    if (!selectedFile) return;
    const athleteId = document.getElementById('upload-athlete').value;
    const date = document.getElementById('upload-date').value || new Date().toISOString().slice(0, 10);
    if (!athleteId) return alert("Selecciona un atleta.");
    const btn = document.getElementById('btn-process');
    btn.disabled = true; btn.textContent = "Procesando...";
    try {
        const storageRef = firebase.storage().ref();
        const path = `gps/${athleteId}/${date}/${selectedFile.name}`;
        await storageRef.child(path).put(selectedFile);
        const processFn = firebase.functions().httpsCallable('process_gps_csv');
        const res = await processFn({ filePath: path, gpsBrand: selectedGpsBrand, brandHints: GPS_BRANDS_DB[selectedGpsBrand]?.metrics || null });
        if (res.data.status === 'success') { alert(`Sincronización Exitosa: ${res.data.ivnLabel}`); showView('dashboard'); } 
        else { alert("Error: " + res.data.message); }
    } catch (e) { console.error(e); alert("Fallo crítico en el motor IVN."); } finally { btn.disabled = false; btn.textContent = "⚡ Procesar y Calcular IVN"; }
}

function populateAthleteSelects() {
    const selects = ['report-athlete-select', 'upload-athlete'];
    const options = '<option value="">Seleccionar Atleta...</option>' + gAthletesCache.sort((a,b)=>a.fullName.localeCompare(b.fullName)).map(a => `<option value="${a.id}">${a.fullName}</option>`).join('');
    selects.forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = options; });
}

function deleteAthlete(id) { if (confirm("¿Eliminar deportista?")) db.collection('athletes').doc(id).delete(); }

function saveSettings() {
    THRESH.iriCritical = parseInt(document.getElementById('threshold-iri').value) || 60;
    THRESH.lapses = parseInt(document.getElementById('threshold-lapses').value) || 2;
    THRESH.iriOptimal = parseInt(document.getElementById('threshold-iri-opt').value) || 85;
    renderDashboard();
    alert("Configuración guardada correctamente.");
}

function refreshData() { location.reload(); }

document.addEventListener('DOMContentLoaded', () => {
    document.documentElement.style.setProperty('overflow-y', 'auto', 'important');
    document.body.style.setProperty('overflow-y', 'auto', 'important');
    const dateEl = document.getElementById('live-date');
    if (dateEl) dateEl.textContent = new Date().toLocaleDateString('es-CL', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
});
