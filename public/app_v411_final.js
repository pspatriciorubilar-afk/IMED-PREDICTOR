/* ═══════════════════════════════════════════
   IMED PREDICTOR — app_v411_final.js
   Version: 4.13.0 (PRECISION & TRANSPARENCY UPDATE)
   Features: Real-time Sync, Integrated IVN, GPS Upload, Trends
   ════════════════════════════════════════════ */

const THRESH = { iriCritical: 60, lapses: 2, iriOptimal: 85 };

// ─── Persistence Logic (Synchronous Load) ───
const savedLocal = localStorage.getItem('imed_predictor_settings');
if (savedLocal) {
    try {
        const parsed = JSON.parse(savedLocal);
        Object.assign(THRESH, parsed);
        console.log("IMED: Configuración local cargada:", THRESH);
    } catch (e) { console.error("Error parsing local settings:", e); }
}

let db, auth;
let unsubscribe = null;
let allPerformance = [];
let gAthletesCache = [];
let correlationChart = null;
let teamTrendChart = null;
let riskDistChart = null;
let reportCharts = [];
let selectedGpsBrand = 'auto';
let selectedFile = null;
let gActiveProfileId = null;
let gSncTeamFilter = "";
let gTriageMode = false;

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
    // ─── Cargar Configuración del Sistema (Persistence) ───
    try {
        const savedLocal = localStorage.getItem('imed_predictor_settings');
        if (savedLocal) Object.assign(THRESH, JSON.parse(savedLocal));

        const configDoc = await db.collection('system_config').doc('thresholds').get();
        if (configDoc.exists) {
            Object.assign(THRESH, configDoc.data());
            localStorage.setItem('imed_predictor_settings', JSON.stringify(THRESH));
        }
    } catch (e) { console.warn("Config Load Error:", e); }

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
    if (viewId === 'settings') {
        document.getElementById('threshold-iri').value = THRESH.iriCritical;
        document.getElementById('threshold-lapses').value = THRESH.lapses;
        document.getElementById('threshold-iri-opt').value = THRESH.iriOptimal;
    }
}

// ─── Engines ───
function calculateWellness(p) {
    const w = p.wellness || {};
    // Si no hay datos de bienestar, retornamos null para que el sistema use el IRI como base neutra
    if (!w.sleepHours && !p.sleep_hours) return null;

    const h = w.sleepHours ?? p.sleep_hours ?? 8;
    const q = w.sleepQuality ?? p.sleep_quality ?? 5;
    const s = w.stressLevel ?? p.stress ?? 1;
    const f = w.fatigueLevel ?? p.fatigue ?? 1;
    const r = w.sorenessLevel ?? p.soreness ?? 1;

    const hScore = (Math.min(8, h) / 8) * 20;
    const qScore = (q / 5) * 20;
    const sScore = ((6 - s) / 5) * 20;
    const fScore = ((6 - f) / 5) * 20;
    const rScore = ((6 - r) / 5) * 20;
    return Math.round(hScore + qScore + sScore + fScore + rScore);
}

function getUnifiedStatus(p) {
    const pvtRaw = Number(p.iri || p.pvt?.metrics?.iri || 0);
    const metrics = p.pvt?.metrics || {};
    const lapses = Number(metrics.lapses ?? p.lapses ?? 0);
    const wellnessRaw = calculateWellness(p);
    
    if (!pvtRaw) {
        return {
            level: 'GRAY', label: 'PENDIENTE', na: 0, wellness: 0, ivn: 0, iri: 0,
            badgeClass: 'badge-gray', ringClass: 'ring-gray'
        };
    }

    // Algoritmo Fiel: Wellness + PVT = IRI (Promedio de disponibilidad)
    // Si no hay wellness, se usa el PVT como base única.
    const wellness = wellnessRaw !== null ? wellnessRaw : pvtRaw;
    const iriFinal = Math.round((pvtRaw + wellness) / 2);
    
    // El NA (Neural Availability) se ve afectado por los lapsos (penalización técnica)
    const na = Math.max(0, iriFinal * (1 - (lapses * 0.1)));
    
    const gps = p.gps || {};
    const decel = gps.decel_high || gps.decel_z5 || 0;
    const sprint = (gps.sprint_dist || gps.sprint_distance || 0) / 10;
    const load = (decel * 0.6) + (sprint * 0.4);
    
    const acwr = p.acwr || 1.0;
    const ivn = na > 0 ? ((load * acwr) / (na / 100)) : load;

    let level = 'GREEN', label = 'ÓPTIMO';
    
    // Lógica de Estados: Basada estrictamente en el IRI FINAL (Wellness + PVT)
    const critIri = THRESH.iriCritical || 60;
    const optIri = THRESH.iriOptimal || 85;
    const maxLapses = THRESH.lapses || 2;

    if (iriFinal < critIri || lapses >= maxLapses || ivn > 30) { 
        level = 'RED'; label = 'RIESGO CRÍTICO'; 
    }
    else if (iriFinal < optIri || ivn > 25) { 
        level = 'YELLOW'; label = 'ADVERTENCIA'; 
    }

    return { 
        level, label, na, wellness, ivn, iri: iriFinal,
        badgeClass: `badge-${level.toLowerCase()}`, 
        ringClass: `ring-${level.toLowerCase()}`,
        action: p.action || ''
    };
}

function calcSNC(p) { return getUnifiedStatus(p); }
function calcIVN(p) { return getUnifiedStatus(p); }
// ─── Triage Mode ───
function toggleTriageMode() {
    gTriageMode = !gTriageMode;
    const btn = document.getElementById('btn-triage-toggle');
    if (btn) {
        if (gTriageMode) {
            btn.innerHTML = 'TRIAJE: ON';
            btn.style.background = 'rgba(255,77,77,0.15)';
            btn.style.color = '#FF4D4D';
            btn.style.borderColor = 'rgba(255,77,77,0.4)';
        } else {
            btn.innerHTML = 'TRIAJE: OFF';
            btn.style.background = 'transparent';
            btn.style.color = 'var(--text-2)';
            btn.style.borderColor = 'var(--border)';
        }
    }
    renderDashboard();
}

// ─── Rendering ───
function renderDashboard() {
    const container = document.getElementById('athlete-list');
    if (!container) return;
    // Usar fecha local para evitar desfases UTC
    const today = new Date().toLocaleDateString('en-CA'); 
    const latest = {};
    
    let todayEvalsCount = 0;
    allPerformance.forEach(p => { 
        if (p.date === today) todayEvalsCount++;
        const aid = String(p.athleteId || "").trim();
        if (aid && !latest[aid]) latest[aid] = p;
    });
    
    const latestList = Object.values(latest);
    let counts = { RED: 0, YELLOW: 0, GREEN: 0 };

    // Triage Filter
    let displayList = latestList;
    if (gTriageMode) {
        displayList = latestList.filter(p => {
            const level = calcIVN(p).level;
            return level === 'RED' || level === 'YELLOW';
        });
    }
    
    container.innerHTML = displayList.length ? displayList.map(p => {
        const ivn = calcIVN(p);
        if (p.date === today) counts[ivn.level]++;
        const initials = (p.athleteName || 'AT').split(' ').map(w => w[0]).join('').slice(0, 2);
        const hasGps = p.gps && (p.gps.decel_high || p.gps.decel_z5 || p.gps.sprint_dist);
        return `
            <div class="athlete-card" onclick="openSncModal('${p.athleteId}')" style="position:relative">
                <div class="athlete-avatar">${initials}<div class="risk-ring ${ivn.ringClass}"></div></div>
                <div class="athlete-info">
                    <div class="athlete-name">${p.athleteName || p.athleteId}</div>
                    <div class="athlete-pos" style="color: var(--text-2); font-size: 0.75rem;">📅 ${p.date ? p.date.split('-').reverse().join('-') : '—'}</div>
                </div>
                <div class="athlete-metrics">
                    <div class="metric-mini"><div class="val">${Math.round(p.iri)}</div><div class="lbl">IRI</div></div>
                    <div class="metric-mini"><div class="val">${p.pvt?.metrics?.lapses ?? p.lapses ?? 0}</div><div class="lbl">LAPSES</div></div>
                    <div class="metric-mini">
                        <div class="val" style="color:${hasGps ? 'var(--blue)' : '#636375'}">${hasGps ? ivn.ivn.toFixed(1)+'x' : 'S/D'}</div>
                        <div class="lbl">${hasGps ? 'INDICE IVN' : 'SIN GPS'}</div>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:10px">
                    <span class="risk-badge ${ivn.badgeClass}">${ivn.label}</span>
                    <button class="btn-delete" style="width:28px; height:28px; padding:0; display:flex; align-items:center; justify-content:center; border-radius:6px; background:rgba(255,69,58,0.1); border:1px solid rgba(255,69,58,0.2); color:#FF453A" onclick="event.stopPropagation(); deleteAthlete('${p.athleteId}')">🗑</button>
                </div>
            </div>`;
    }).join('') : '<div class="empty-state">No hay evaluaciones registradas hoy.</div>';
    
    if(document.getElementById('count-critical')) document.getElementById('count-critical').textContent = counts.RED;
    if(document.getElementById('count-warning')) document.getElementById('count-warning').textContent = counts.YELLOW;
    if(document.getElementById('count-optimal')) document.getElementById('count-optimal').textContent = counts.GREEN;
    
    if(document.getElementById('kpi-critical')) document.getElementById('kpi-critical').textContent = counts.RED;
    if(document.getElementById('kpi-coordination')) document.getElementById('kpi-coordination').textContent = counts.YELLOW;
    if(document.getElementById('kpi-optimal')) document.getElementById('kpi-optimal').textContent = counts.GREEN;
    if(document.getElementById('kpi-total')) document.getElementById('kpi-total').textContent = todayEvalsCount;

    updateChart();
    updateAnalyticsCharts();
}

function updateAnalyticsCharts() {
    const trendCtx = document.getElementById('teamTrendChart');
    const riskCtx = document.getElementById('riskDistributionChart');
    if (!trendCtx || !riskCtx) return;

    // Obtener los días seleccionados del filtro
    const days = parseInt(document.getElementById('chart-filter')?.value || 7);
    const labels = [];
    for (let i = days - 1; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        labels.push(d.toLocaleDateString('en-CA'));
    }

    // --- 1. Tendencias por Equipo ---
    const teams = [...new Set(gAthletesCache.map(a => a.team || 'SNC'))];
    const teamDatasets = teams.map((team, idx) => {
        const colors = ['#00E5FF', '#BF5AF2', '#32D74B', '#FF9F0A', '#FF4D4D'];
        const color = colors[idx % colors.length];
        
        const data = labels.map(day => {
            const dayRecords = allPerformance.filter(p => {
                const ath = gAthletesCache.find(a => String(a.id).trim() === String(p.athleteId).trim());
                return p.date === day && ath && (ath.team || 'SNC') === team;
            });
            if (!dayRecords.length) return null;
            const avg = dayRecords.reduce((acc, r) => acc + getUnifiedStatus(r).iri, 0) / dayRecords.length;
            return Math.round(avg);
        });

        return {
            label: team,
            data: data,
            borderColor: color,
            backgroundColor: 'transparent',
            tension: 0.4,
            borderWidth: 3,
            pointRadius: 3,
            spanGaps: true
        };
    });

    if (teamTrendChart) teamTrendChart.destroy();
    teamTrendChart = new Chart(trendCtx, {
        type: 'line',
        data: { labels, datasets: teamDatasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'top', labels: { color: '#636375', font: { size: 10 } } } },
            scales: {
                y: { min: 40, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#636375' } },
                x: { grid: { display: false }, ticks: { color: '#636375' } }
            }
        }
    });

    // --- 2. Distribución de Riesgo (Stacked Area) ---
    const riskDatasets = [
        { label: 'ÓPTIMO', color: '#32D74B', level: 'GREEN' },
        { label: 'ADVERTENCIA', color: '#FFD60A', level: 'YELLOW' },
        { label: 'RIESGO CRÍTICO', color: '#FF4D4D', level: 'RED' }
    ].map(r => {
        const data = labels.map(day => {
            return allPerformance.filter(p => p.date === day && getUnifiedStatus(p).level === r.level).length;
        });
        return {
            label: r.label,
            data: data,
            borderColor: r.color,
            backgroundColor: r.color + '22',
            fill: true,
            tension: 0.4,
            borderWidth: 2
        };
    });

    if (riskDistChart) riskDistChart.destroy();
    riskDistChart = new Chart(riskCtx, {
        type: 'line',
        data: { labels, datasets: riskDatasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'top', labels: { color: '#636375', font: { size: 10 } } } },
            scales: {
                y: { stacked: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#636375', precision: 0 } },
                x: { grid: { display: false }, ticks: { color: '#636375' } }
            }
        }
    });
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
    
    // Sincronizar actualización de los otros gráficos
    updateAnalyticsCharts();
}

function renderSncTable() {
    const list = document.getElementById('snc-athletes-list');
    if (!list) return;
    // Usar la fecha local (YYYY-MM-DD) para evitar desfases de zona horaria con UTC
    const today = new Date().toLocaleDateString('en-CA'); 
    
    // Filtro por equipo/plantilla
    const filteredAthletes = gSncTeamFilter 
        ? gAthletesCache.filter(a => a.team === gSncTeamFilter)
        : gAthletesCache;

    list.innerHTML = filteredAthletes.map(a => {
        const records = allPerformance.filter(p => String(p.athleteId).trim() === String(a.id).trim());
        const p = records[0]; // El más reciente (está ordenado desc)
        const snc = p ? calcSNC(p) : { level: 'GRAY', label: 'PENDIENTE', badgeClass: 'badge-gray' };
        
        // Fix Hoy: Buscar si alguno de los registros es de hoy
        const isDone = records.some(x => x.date === today);
        
        // Sesiones totales
        const sessionCount = records.length;

        // Tendencia dinámica
        const tendency = calcTendency(records);
        
        // Desviación de Latencia dinámica
        const latDev = calcLatencyDev(p, records);

        return `
            <tr onclick="openSncModal('${a.id}')">
                <td><strong>${a.fullName}</strong></td>
                <td><span class="badge badge-gray">${a.team || 'SNC'}</span></td>
                <td><strong class="num-mono" style="font-size:15px">${p ? Math.round(snc.iri) : '—'}</strong></td>
                <td><span class="risk-badge ${snc.badgeClass}">${snc.label}</span></td>
                <td><span class="risk-badge ${latDev.class}">${latDev.label}</span></td>
                <td><span class="risk-badge ${tendency.class}">${tendency.label}</span></td>
                <td style="white-space:nowrap" class="num-mono">${p ? p.date.split('-').reverse().join('-') : '—'}</td>
                <td>
                    <span class="num-mono" style="color:${p?.gps ? 'var(--blue)' : '#636375'}; font-size:14px">
                        ${p?.gps ? (snc.ivn.toFixed(1) + 'x') : '<small style="opacity:0.5">S/D GPS</small>'}
                    </span>
                </td>
                <td class="num-mono">${p?.timestamp ? (p.timestamp.seconds ? new Date(p.timestamp.seconds*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}) : '—') : '—'}</td>
                <td><span class="badge badge-gray num-mono" style="background:rgba(0,229,255,0.1); color:#00E5FF">${sessionCount}</span></td>
                <td><span class="risk-badge ${isDone ? 'badge-green' : 'badge-gray'}" style="width:32px; text-align:center">${isDone ? 'SI' : 'NO'}</span></td>
                <td><button class="btn-mini">Análisis</button></td>
                <td style="display:flex; gap:8px; align-items:center; min-width:110px">
                    <button class="btn-mini" style="background:#BF5AF222; color:#BF5AF2; border:1px solid #BF5AF244" onclick="event.stopPropagation(); exportAthletePDF('${a.id}')">PDF</button>
                    <button class="btn-delete" onclick="event.stopPropagation(); deleteAthlete('${a.id}')">🗑</button>
                </td>
            </tr>`;
    }).join('');
}

function calcTendency(records) {
    if (records.length < 2) return { label: 'ESTABLE', class: 'badge-green' };
    const latest = records[0].iri || 0;
    const prev = records[1].iri || 0;
    const diff = latest - prev;
    if (diff > 5) return { label: 'MEJORA', class: 'badge-green' };
    if (diff < -5) return { label: 'CAÍDA', class: 'badge-red' };
    return { label: 'ESTABLE', class: 'badge-green' };
}

function calcLatencyDev(p, records) {
    if (!p || records.length < 3) return { label: 'NORMAL', class: 'badge-green' };
    const current = p.pvt?.metrics?.meanLatency ?? p.avg_reaction ?? 280;
    const history = records.slice(1, 10).map(r => r.pvt?.metrics?.meanLatency ?? r.avg_reaction ?? 280);
    const avg = history.reduce((a,b)=>a+b,0) / history.length;
    if (current > avg * 1.15) return { label: 'ALTA', class: 'badge-red' };
    if (current > avg * 1.05) return { label: 'LEVE', class: 'badge-yellow' };
    return { label: 'NORMAL', class: 'badge-green' };
}

function renderAthletesTable(f = '') {
    const container = document.getElementById('athletes-grouped-container');
    if (!container) return;

    // Agrupar atletas por equipo
    const grouped = {};
    gAthletesCache.filter(a => a.fullName.toLowerCase().includes(f.toLowerCase()) || (a.team || '').toLowerCase().includes(f.toLowerCase())).forEach(a => {
        const teamName = a.team || 'SIN EQUIPO / GENERAL';
        if (!grouped[teamName]) grouped[teamName] = [];
        grouped[teamName].push(a);
    });

    const teams = Object.keys(grouped).sort();

    container.innerHTML = teams.length ? teams.map(team => `
        <div class="report-card" style="margin-bottom:30px">
            <div class="panel-header" style="border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom:15px; margin-bottom:15px">
                <div>
                    <div class="panel-label">PLANTILLA</div>
                    <h2 class="panel-title" style="color:var(--blue)">${team}</h2>
                </div>
                <div class="panel-label">${grouped[team].length} ATLETAS</div>
            </div>
            <div class="table-container">
                <table class="athletes-table">
                    <thead>
                        <tr>
                            <th>ATLETA</th>
                            <th>ESTADO</th>
                            <th>ÚLT. EVALUACIÓN</th>
                            <th>ESTADO SNC</th>
                            <th>FICHA</th>
                            <th>BORRAR</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${grouped[team].map(a => {
                            const lastEval = allPerformance.find(p => String(p.athleteId).trim() === String(a.id).trim());
                            const status = lastEval ? calcSNC(lastEval) : { level: 'GRAY', label: 'SIN DATOS', badgeClass: 'badge-gray' };
                            return `
                                <tr onclick="openAthleteProfile('${a.id}')">
                                    <td>
                                        <div style="display:flex; align-items:center; gap:10px">
                                            <div class="athlete-avatar" style="width:30px; height:30px; font-size:10px">${a.fullName.charAt(0)}</div>
                                            <strong>${a.fullName}</strong>
                                        </div>
                                    </td>
                                    <td><span class="risk-badge ${status.badgeClass}">${status.label}</span></td>
                                    <td>${lastEval ? lastEval.date : '—'}</td>
                                    <td>${lastEval ? `IRI: ${Math.round(status.iri)}` : 'Pendiente'}</td>
                                    <td style="display:flex; gap:5px; align-items:center;">
                                        <button class="btn-mini">Ficha Completa</button>
                                        <button class="btn-mini" style="background:rgba(50,215,75,0.1); color:#32D74B; border-color:rgba(50,215,75,0.2)" onclick="event.stopPropagation(); editAthleteNotes('${a.id}')">Editar Ficha</button>
                                    </td>
                                    <td><button class="btn-delete" onclick="event.stopPropagation(); deleteAthlete('${a.id}')">🗑</button></td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `).join('') : '<div class="empty-state">No se encontraron atletas con ese filtro.</div>';
}

function filterAthletes(v) { renderAthletesTable(v); }

// ─── Modals ───
async function openAthleteProfile(id) {
    gActiveProfileId = id;
    const a = gAthletesCache.find(x => x.id === id);
    if (!a) return;

    // Calcular estadísticas históricas para enriquecer la ficha
    const records = allPerformance.filter(p => String(p.athleteId).trim() === String(id).trim());
    const avgIri = records.length ? Math.round(records.reduce((acc, p) => acc + (p.iri || 0), 0) / records.length) : '—';
    const avgLat = records.length ? Math.round(records.reduce((acc, p) => acc + (p.pvt?.metrics?.meanLatency ?? p.avg_reaction ?? 0), 0) / records.length) : '—';
    const totalEvals = records.length;

    document.getElementById('prof-static-name').textContent = a.fullName;
    document.getElementById('prof-static-pos').textContent = a.position || 'Deportista de Élite';
    
    document.getElementById('tab-container-ficha').innerHTML = `
        <div class="grid-2col" style="margin-top:20px; gap:15px">
            <div class="panel glass" style="border-left: 3px solid var(--blue)">
                <div class="panel-label">EQUIPO ACTUAL</div>
                <div class="panel-title">${a.team || 'Sin Equipo'}</div>
                <button class="btn-mini" onclick="promptTeamChange('${a.id}', '${a.team || ''}')" style="margin-top:10px; width:100%">⚙️ Cambiar Plantilla</button>
            </div>
            <div class="panel glass" style="border-left: 3px solid var(--green)">
                <div class="panel-label">ESTADO DE SALUD</div>
                <div class="panel-title">DISPONIBLE</div>
            </div>
        </div>

        <div class="panel-header" style="margin-top:25px">
            <div>
                <div class="panel-label">MÉTRICAS HISTÓRICAS (PROMEDIO)</div>
                <h2 class="panel-title">Perfil Biométrico de Rendimiento</h2>
            </div>
        </div>

        <div class="modal-grid-stats" style="margin-top:15px">
            <div class="stat-card-mini"><div class="val">${avgIri}</div><div class="lbl">PROM. IRI</div></div>
            <div class="stat-card-mini"><div class="val">${avgLat}ms</div><div class="lbl">LAT. MEDIA</div></div>
            <div class="stat-card-mini"><div class="val">${totalEvals}</div><div class="lbl">TOTAL EVALS</div></div>
        </div>

        <div class="panel glass" style="margin-top:20px">
            <div class="panel-label">NOTAS DE SEGUIMIENTO TÉCNICO</div>
            <p style="font-size:13px; color:var(--text-2); line-height:1.5">${a.notes || 'No hay notas técnicas registradas para este atleta. Utilice este espacio para documentar observaciones de campo o recomendaciones de rendimiento.'}</p>
        </div>
        
        <div style="margin-top:20px; display:flex; gap:10px">
            <button class="btn-primary" onclick="viewAthleteTrends('${a.id}')" style="flex:1; background:var(--blue-dim); color:var(--blue); border:1px solid var(--blue)">📊 Ver Análisis de Tendencia</button>
            <button class="btn-primary" onclick="exportAthletePDF('${a.id}')" style="flex:1; background:rgba(255,255,255,0.05); border:1px solid var(--border)">📄 Exportar Reporte PDF</button>
        </div>
    `;
    document.getElementById('athlete-profile-modal').classList.remove('hidden');
}

async function exportAthletePDF(id) {
    const a = gAthletesCache.find(x => x.id === id);
    if (!a) return;
    
    // Obtener y procesar registros
    const records = allPerformance
        .filter(p => String(p.athleteId).trim() === String(id).trim())
        .sort((a,b) => new Date(b.date) - new Date(a.date));
    
    const latest = records[0] ? getUnifiedStatus(records[0]) : null;
    const historyData = records.slice(0, 7).reverse(); // Para el gráfico (últimos 7 días)
    
    // Calcular promedio del IRI Final
    const totalIriSum = records.reduce((acc, p) => acc + (getUnifiedStatus(p).iri || 0), 0);
    const avgIri = records.length ? Math.round(totalIriSum / records.length) : '—';

    // Generar conclusiones dinámicas basadas en el algoritmo
    let conclusionText = "El deportista presenta una disponibilidad neural óptima. Se recomienda continuar con el plan de entrenamiento programado sin restricciones.";
    let conclusionColor = "#32D74B";

    if (latest) {
        if (latest.level === 'RED') {
            conclusionText = "ALERTA CRÍTICA: Se detecta un alto riesgo de vulnerabilidad neuro-mecánica. Es imperativo reducir la carga mecánica (desaceleraciones) y priorizar la recuperación biológica inmediata.";
            conclusionColor = "#FF4D4D";
        } else if (latest.level === 'YELLOW') {
            conclusionText = "ADVERTENCIA: El índice IRI se encuentra por debajo del umbral óptimo o se detecta fatiga acumulada. Se recomienda moderar tareas de alta precisión y monitorear la calidad del sueño.";
            conclusionColor = "#FFD60A";
        }
        
        // Agregar nota específica sobre lapses o IVN si aplica
        if (latest.ivn > 25) conclusionText += " El elevado índice IVN sugiere una desproporción entre la carga mecánica y la capacidad de recuperación actual.";
    }

    const element = document.createElement('div');
    element.style.padding = '40px';
    element.style.width = '750px';
    element.style.background = '#0a0c0f';
    element.style.color = '#ffffff';
    element.style.fontFamily = 'Inter, sans-serif';

    // Preparar filas de historia (incluyendo todos los pilares de wellness y ex-gaussian)
    const historyRows = records.slice(0, 6).map(r => {
        const st = getUnifiedStatus(r);
        const aa = r.advanced_analysis || {};
        const mu = aa.mu_ms != null ? aa.mu_ms.toFixed(1) : '—';
        const sigma = aa.sigma_ms != null ? aa.sigma_ms.toFixed(1) : '—';
        const tau = aa.tau_ms != null ? aa.tau_ms.toFixed(1) : '—';
        const tauZ = aa.tau_zscore != null ? aa.tau_zscore.toFixed(2) : '—';
        const wellnessVal = calculateWellness(r) != null ? calculateWellness(r) : '—';
        const wZ = aa.wellness_zscore != null ? aa.wellness_zscore.toFixed(2) : '—';

        return `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05)">
                <td style="padding:10px 0; font-size:10px">${r.date}</td>
                <td style="padding:10px 0; font-size:11px; color:${st.level==='RED'?'#FF4D4D':(st.level==='YELLOW'?'#FFD60A':'#32D74B')}; font-weight:bold">${st.iri}%</td>
                <td style="padding:10px 0; font-size:10px">${mu}</td>
                <td style="padding:10px 0; font-size:10px">${sigma}</td>
                <td style="padding:10px 0; font-size:10px">${tau}</td>
                <td style="padding:10px 0; font-size:10px; color:${tauZ !== '—' && Number(tauZ) > 1.5 ? '#FF4D4D' : (tauZ !== '—' && Number(tauZ) > 1.0 ? '#FFD60A' : '#32D74B')}">${tauZ}</td>
                <td style="padding:10px 0; font-size:10px">${wellnessVal}%</td>
                <td style="padding:10px 0; font-size:10px; color:${wZ !== '—' && Number(wZ) < -1.2 ? '#FF4D4D' : (wZ !== '—' && Number(wZ) < -0.8 ? '#FFD60A' : '#32D74B')}">${wZ}</td>
            </tr>
        `;
    }).join('');

    element.innerHTML = `
        <div style="border-bottom: 2px solid #00E5FF; padding-bottom: 20px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center">
            <div>
                <h1 style="margin:0; font-size: 24px; color: #00E5FF; letter-spacing:-0.5px">IMED PREDICTOR — REPORTE ÉLITE</h1>
                <p style="margin:5px 0 0; font-size: 11px; color: #636375; font-weight:700; letter-spacing:1.5px">SISTEMA DE NEURO-INTELIGENCIA DEPORTIVA</p>
            </div>
            <div style="text-align: right">
                <p style="margin:0; font-size: 18px; font-weight: 900; color:#fff">${a.fullName.toUpperCase()}</p>
                <p style="margin:5px 0 0; font-size: 10px; color: #00E5FF; font-weight:700">${a.team || 'SNC'}</p>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 25px">
            <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); text-align:center">
                <div style="font-size:9px; color:#636375; margin-bottom:5px; font-weight:700">IRI ACTUAL (PROCESADO)</div>
                <div style="font-size:22px; font-weight:900; color:${conclusionColor}">${latest ? latest.iri+'%' : 'PENDIENTE'}</div>
            </div>
            <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); text-align:center">
                <div style="font-size:9px; color:#636375; margin-bottom:5px; font-weight:700">PROM. HISTÓRICO</div>
                <div style="font-size:22px; font-weight:900; color:#fff">${avgIri}%</div>
            </div>
            <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); text-align:center">
                <div style="font-size:9px; color:#636375; margin-bottom:5px; font-weight:700">ESTADO DE RIESGO</div>
                <div style="font-size:12px; font-weight:900; color:${conclusionColor}; margin-top:8px">${latest ? latest.label : 'N/A'}</div>
            </div>
        </div>

        <div style="margin-bottom: 25px; background: rgba(255,255,255,0.02); padding:20px; border-radius:12px; border:1px solid rgba(255,255,255,0.05)">
            <h3 style="font-size: 11px; color:#00E5FF; margin-top:0; margin-bottom:15px; font-weight:800; letter-spacing:1px">EVOLUCIÓN HISTÓRICA DEL IRI</h3>
            <canvas id="pdf-chart" width="700" height="180"></canvas>
        </div>

        <div style="margin-bottom: 25px">
            <h3 style="font-size: 11px; color:#00E5FF; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; margin-bottom:15px; font-weight:800; letter-spacing:1px">DESGLOSE DE BIOMARCADORES (ÚLTIMAS SESIONES)</h3>
            <table style="width:100%; border-collapse: collapse; text-align:left">
                <thead>
                    <tr style="color:#636375; font-size:9px; text-transform:uppercase; border-bottom: 1px solid rgba(255,255,255,0.1)">
                        <th style="padding-bottom:10px">Fecha</th>
                        <th style="padding-bottom:10px">IRI Final</th>
                        <th style="padding-bottom:10px">mu (ms)</th>
                        <th style="padding-bottom:10px">sigma (ms)</th>
                        <th style="padding-bottom:10px">tau (ms)</th>
                        <th style="padding-bottom:10px">tau Z-Score</th>
                        <th style="padding-bottom:10px">Wellness</th>
                        <th style="padding-bottom:10px">Wellness Z-Score</th>
                    </tr>
                </thead>
                <tbody>${historyRows}</tbody>
            </table>
        </div>

        <div style="margin-bottom: 20px">
            <h3 style="font-size: 11px; color:#00E5FF; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; margin-bottom:10px; font-weight:800; letter-spacing:1px">CONCLUSIONES Y RECOMENDACIONES DE RENDIMIENTO</h3>
            <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 10px; font-size: 12px; line-height: 1.6; color: #fff; border: 1px solid ${conclusionColor}44">
                <strong style="color:${conclusionColor}">DIAGNÓSTICO:</strong> ${conclusionText}
                <p style="margin-top:10px; color:#8a8a9e; font-size:11px"><em>*Este informe ha sido generado automáticamente por el motor de inteligencia IMED Predictor basado en el algoritmo de Vulnerabilidad Neuro-Mecánica.</em></p>
            </div>
        </div>

        <div style="margin-top: 30px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px; display:flex; justify-content:space-between; align-items:center">
            <div style="font-size: 9px; color: #444452">UID: ${id} | AUTH: IMED_SYSTEM_v4</div>
            <div style="font-size: 9px; color: #636375; text-align:right">© 2026 IMED PREDICTOR — TECNOLOGÍA NEURO-MECÁNICA</div>
        </div>
    `;

    document.body.appendChild(element);

    // Renderizar gráfico para el PDF
    const ctx = element.querySelector('#pdf-chart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: historyData.map(d => d.date),
            datasets: [{
                label: 'IRI Evolución',
                data: historyData.map(d => getUnifiedStatus(d).iri),
                borderColor: '#00E5FF',
                backgroundColor: 'rgba(0, 229, 255, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#00E5FF',
                fill: true
            }]
        },
        options: {
            responsive: false,
            animation: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#636375', font: { size: 9 } } },
                x: { grid: { display: false }, ticks: { color: '#636375', font: { size: 9 } } }
            }
        }
    });

    const opt = {
        margin: [0, 0],
        filename: `Reporte_Elite_IMED_${a.fullName.replace(/\\s+/g, '_')}.pdf`,
        image: { type: 'jpeg', quality: 1.0 },
        html2canvas: { scale: 2, backgroundColor: '#0a0c0f', useCORS: true },
        jsPDF: { unit: 'px', format: [792, 1056], hotfixes: ['px_scaling'] }
    };

    try {
        await html2pdf().set(opt).from(element).save();
    } finally {
        document.body.removeChild(element);
    }
}

async function deleteAthlete(id) {
    if (!confirm('¿Estás seguro de que deseas eliminar este deportista y todos sus registros? Esta acción no se puede deshacer.')) return;
    
    try {
        // 1. Eliminar de la colección 'athletes'
        await db.collection('athletes').doc(id).delete();
        
        // 2. Eliminar registros de 'performance' asociados
        const snapshot = await db.collection('performance').where('athleteId', '==', id).get();
        const batch = db.batch();
        snapshot.docs.forEach(doc => batch.delete(doc.ref));
        await batch.commit();
        
        alert('Deportista eliminado correctamente.');
        // Recargar datos (los listeners de Firestore se encargarán del resto si están activos, 
        // pero aquí forzamos una actualización de la UI si es necesario)
    } catch (e) {
        console.error("Error al eliminar deportista:", e);
        alert('Error al intentar eliminar el deportista.');
    }
}

async function promptTeamChange(id, currentTeam) {
    const newTeam = prompt("Ingrese el nombre de la nueva Plantilla/Equipo:", currentTeam);
    if (newTeam !== null) {
        try {
            await db.collection('athletes').doc(id).update({ team: newTeam });
            alert("Atleta re-asignado con éxito.");
            // La recarga se activará por el listener onSnapshot
        } catch (e) {
            console.error(e);
            alert("Error al actualizar el equipo.");
        }
    }
}

async function editAthleteNotes(id) {
    const a = gAthletesCache.find(x => x.id === id);
    if (!a) return;
    const newNotes = prompt("Anotaciones y Seguimiento Técnico (Máximo 500 caracteres recomendados):", a.notes || "");
    if (newNotes !== null) {
        try {
            await db.collection('athletes').doc(id).update({ notes: newNotes });
            // El listener onSnapshot recargará la vista automáticamente
        } catch (e) {
            console.error(e);
            alert("Error al guardar las notas.");
        }
    }
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
                ${renderDetailRow('Lapsos de Atención', pvt.lapses ?? p.lapses ?? 0, '/ 30 ensayos', 30, '#FF4D4D')}
            </div>
            <div class="detail-box">
                <div class="detail-box-header">💤 WELLNESS — ESTADO SUBJETIVO</div>
                ${renderDetailRow('Horas de Sueño', p.wellness?.sleepHours ?? p.sleep_hours ?? 7, 'h', 10, '#32D74B')}
                ${renderDetailRow('Calidad de Sueño', p.wellness?.sleepQuality ?? p.sleep_quality ?? 3, '/5', 5, '#FFD60A')}
                ${renderDetailRow('Nivel de Estrés', p.wellness?.stressLevel ?? p.stress ?? 2, '/5', 5, '#FF4D4D')}
                ${renderDetailRow('Fatiga Percibida', p.wellness?.fatigueLevel ?? p.fatigue ?? 2, '/5', 5, '#FFD60A')}
            </div>
        </div>
        ${renderExGaussPanel(p)}
        <div class="prescription-box">
            <div class="prescription-title">⚡ DIAGNÓSTICO INTEGRADO NA-GPS — PRESCRIPCIÓN</div>
            <div class="prescription-text">
                <strong>Estado: ${snc.label}.</strong> Disponibilidad Neural Integrada: <strong>${Math.round(snc.na)}%</strong>. 
                El algoritmo ha detectado una correlación entre ${snc.wellness < 70 ? 'un Wellness pobre' : 'fatiga neural'} 
                y una carga mecánica de <strong>${snc.ivn.toFixed(1)}x</strong>.
                ${p.acwr ? `<br>Ratio de Carga Aguda (ACWR): <strong>${p.acwr.toFixed(2)}</strong>` : ''}
                <br><br>
                <strong>Prescripción:</strong> ${snc.action || (snc.level === 'GREEN' ? 'Mantener cargas. Atleta en zona de adaptación.' : (snc.level === 'YELLOW' ? 'Moderar intensidad mecánica. Evitar sprints máximos.' : 'REDUCCIÓN INMEDIATA. Riesgo de lesión elevado por baja disponibilidad neural.'))}
                
                <div style="margin-top:15px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.1); font-size:11px; color:var(--text-3); line-height:1.5; font-style: italic">
                    <strong>Desglose Técnico de Variables:</strong><br>
                    • <strong>Disponibilidad Neural (NA):</strong> Cálculo balanceado entre IRI (60%) y Wellness (40%), ajustado por precisión cognitiva (Lapses).<br>
                    • <strong>Carga Mecánica (CM):</strong> Índice de intensidad física derivado de Desaceleraciones (60%) y Sprints normalizados (40%).<br>
                    • <strong>ACWR:</strong> Ratio de carga aguda vs. crónica; detecta picos de esfuerzo peligrosos sobre la base histórica.<br>
                    • <strong>Algoritmo IVN:</strong> Resultado de cruzar la CM y el ACWR contra la Disponibilidad Neural para predecir fatiga neuro-mecánica.
                </div>
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

/**
 * Panel de Análisis Ex-Gaussiano — Análisis Distribucional Avanzado
 * Renderiza μ, σ, τ y Z-scores si advanced_analysis existe en el documento.
 * Implementa fallbacks resilientes para evitar crashes cuando el worker
 * aún no ha procesado al atleta (datos insuficientes o primer día).
 */
function renderExGaussPanel(p) {
    const aa = p?.advanced_analysis;

    // ── Sin datos: mostrar estado de calibración ──
    if (!aa || (aa.status === 'INSUFFICIENT_TRIALS' && aa.mu_ms == null)) {
        const n = aa?.n_trials ?? p?.pvt?.metrics?.trials?.length ?? '?';
        return `
        <div class="prescription-box" style="border-left: 3px solid #636375; margin-bottom: 12px">
            <div class="prescription-title" style="color:#636375">🔬 ANÁLISIS EX-GAUSSIANO — CALIBRANDO</div>
            <div class="prescription-text" style="font-size:12px; color:var(--text-3)">
                El análisis distribucional avanzado (μ, σ, τ) requiere <strong>≥ 20 trials PVT</strong> por sesión.<br>
                Trials registrados hoy: <strong>${n}</strong>. 
                El worker procesará este atleta cuando tenga suficientes datos.<br>
                <em style="opacity:0.5">Protocolo PVT-B activo: se requieren 30 estímulos por sesión.</em>
            </div>
        </div>`;
    }

    // ── Panel con datos Ex-Gaussianos ──
    const mu    = aa.mu_ms    != null ? aa.mu_ms.toFixed(1)    : '—';
    const sigma = aa.sigma_ms != null ? aa.sigma_ms.toFixed(1) : '—';
    const tau   = aa.tau_ms   != null ? aa.tau_ms.toFixed(1)   : '—';
    const n     = aa.n_trials ?? '—';

    const tauZ  = aa.tau_zscore      != null ? aa.tau_zscore.toFixed(2)      : null;
    const wZ    = aa.wellness_zscore  != null ? aa.wellness_zscore.toFixed(2) : null;
    const baseN = aa.tau_baseline_n   ?? 0;

    // Color del τ según Z-score
    const tauColor = tauZ == null ? '#636375'
        : tauZ > 1.5 ? '#FF4D4D'
        : tauZ > 1.0 ? '#FFD60A'
        : '#32D74B';

    // Color del status del semáforo Ex-Gaussiano
    const statusColor = aa.readiness_status === 'RED'    ? '#FF4D4D'
                      : aa.readiness_status === 'YELLOW' ? '#FFD60A'
                      : aa.readiness_status === 'GREEN'  ? '#32D74B'
                      : '#636375';

    const zScoreRow = (tauZ || wZ) ? `
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px">
            <div style="background:rgba(255,255,255,0.03); border-radius:8px; padding:10px; text-align:center">
                <div style="font-size:9px; color:#636375; font-weight:700; margin-bottom:4px">τ Z-SCORE (21d)</div>
                <div style="font-size:20px; font-weight:900; color:${tauColor}">${tauZ ?? '—'}</div>
                <div style="font-size:9px; color:#636375; margin-top:2px">base: ${baseN} sesiones</div>
            </div>
            <div style="background:rgba(255,255,255,0.03); border-radius:8px; padding:10px; text-align:center">
                <div style="font-size:9px; color:#636375; font-weight:700; margin-bottom:4px">WELLNESS Z-SCORE</div>
                <div style="font-size:20px; font-weight:900; color:${wZ != null && wZ < -0.8 ? '#FFD60A' : '#32D74B'}">${wZ ?? '—'}</div>
                <div style="font-size:9px; color:#636375; margin-top:2px">ventana 21 días</div>
            </div>
        </div>` : `<div style="font-size:11px; color:#636375; margin-top:10px; font-style:italic">Z-scores disponibles después de 5 sesiones históricas.</div>`;

    return `
    <div class="prescription-box" style="border-left: 3px solid #BF5AF2; margin-bottom:12px">
        <div class="prescription-title" style="color:#BF5AF2">🔬 ANÁLISIS EX-GAUSSIANO — DISTRIBUCIÓN ATENCIONAL</div>
        <div class="prescription-text">

            <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:4px">
                <div style="background:rgba(255,255,255,0.03); border-radius:8px; padding:10px; text-align:center">
                    <div style="font-size:9px; color:#636375; font-weight:700; margin-bottom:4px">μ (VELOCIDAD MOTORA)</div>
                    <div style="font-size:18px; font-weight:900; color:#00E5FF">${mu}<span style="font-size:10px">ms</span></div>
                </div>
                <div style="background:rgba(255,255,255,0.03); border-radius:8px; padding:10px; text-align:center">
                    <div style="font-size:9px; color:#636375; font-weight:700; margin-bottom:4px">σ (CONSISTENCIA)</div>
                    <div style="font-size:18px; font-weight:900; color:#FF9F0A">${sigma}<span style="font-size:10px">ms</span></div>
                </div>
                <div style="background:rgba(255,255,255,0.03); border-radius:8px; padding:10px; text-align:center">
                    <div style="font-size:9px; color:#636375; font-weight:700; margin-bottom:4px">τ (FATIGA CENTRAL / COLA)</div>
                    <div style="font-size:18px; font-weight:900; color:${tauColor}">${tau}<span style="font-size:10px">ms</span></div>
                </div>
            </div>
            <div style="font-size:10px; color:#636375; margin-bottom:8px; font-style:italic">
                Ajuste Ex-Gaussiano MLE sobre ${n} trials · Basner &amp; Dinges (2011)
            </div>

            <div style="margin-top:10px; margin-bottom:12px; font-size:11px; line-height:1.4; color:var(--text-2); background:rgba(255,255,255,0.02); padding:10px; border-radius:8px">
                <strong style="color:var(--text-1)">Traducción de Variables:</strong><br>
                • <strong>μ (Velocidad Motora):</strong> Tiempo de reacción puro del atleta en óptimo estado (velocidad base de procesamiento).<br>
                • <strong>σ (Consistencia):</strong> Varianza en torno a la velocidad base. A menor valor, mayor estabilidad mental y enfoque.<br>
                • <strong>τ (Fatiga Central):</strong> Frecuencia de micro-lapsos atencionales y fatiga acumulada en la corteza (la "cola" del tiempo de reacción). Es el indicador principal de riesgo y sobreentrenamiento del SNC.
            </div>

            ${zScoreRow}

            ${aa.exg_alert ? `
            <div style="margin-top:12px; padding:10px; border-radius:8px; background:${statusColor}18; border:1px solid ${statusColor}44; font-size:12px; color:${statusColor}; line-height:1.5">
                ${aa.exg_alert}
            </div>` : ''}
        </div>
    </div>`;
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
    const qualityVals = records.map(p => p.wellness?.sleepQuality ?? p.sleep_quality ?? 0);

    const muVals = records.map(p => p.advanced_analysis?.mu_ms ?? null);
    const sigmaVals = records.map(p => p.advanced_analysis?.sigma_ms ?? null);
    const tauVals = records.map(p => p.advanced_analysis?.tau_ms ?? null);

    container.innerHTML = `
        <div class="report-grid">
            ${renderReportCard('EVOLUCIÓN IRI (SNC)', 'chart-iri')}
            ${renderReportCard('LATENCIA SNC (MS)', 'chart-latency')}
            
            ${renderReportCard(
                'EX-GAUSSIAN: μ - VELOCIDAD MOTORA BASE', 
                'chart-mu', 
                '<strong>μ (Velocidad Motora):</strong> Tiempo de reacción puro del atleta en óptimo estado (velocidad base de procesamiento). Menores valores representan una mayor frescura motora.'
            )}
            ${renderReportCard(
                'EX-GAUSSIAN: σ - VARIABILIDAD COGNITIVA', 
                'chart-sigma', 
                '<strong>σ (Consistencia):</strong> Desviación o variabilidad en torno al tiempo base. Mide la estabilidad de foco; valores bajos reflejan alta consistencia y enfoque mental.'
            )}
            ${renderReportCard(
                'EX-GAUSSIAN: τ - FATIGA CENTRAL DEL SNC', 
                'chart-tau', 
                '<strong>τ (Fatiga Central):</strong> Indica la frecuencia de micro-lapsos atencionales y fatiga acumulada en la corteza. El aumento de τ es el indicador clave de rendimiento del SNC.'
            )}

            ${renderReportCard('CORRELACIÓN: IRI VS DESACELERACIONES', 'chart-corr')}
            ${renderReportCard('HORAS SUEÑO', 'chart-sleep')}
            ${renderReportCard('CALIDAD SUEÑO (1-5)', 'chart-quality')}
            ${renderReportCard('ESTRÉS', 'chart-stress')}
        </div>`;
    advancedContainer.innerHTML = '';

    createMiniChart('chart-iri', labels, iriVals, '#BF5AF2', 0, 100);
    createMiniChart('chart-latency', labels, latencyVals, '#00E5FF', 200, 450);
    
    createMiniChart('chart-mu', labels, muVals, '#00E5FF', 100, 350);
    createMiniChart('chart-sigma', labels, sigmaVals, '#FF9F0A', 0, 80);
    createMiniChart('chart-tau', labels, tauVals, '#BF5AF2', 0, 150);

    createMiniChart('chart-sleep', labels, sleepVals, '#32D74B', 4, 12);
    createMiniChart('chart-quality', labels, qualityVals, '#FF9F0A', 1, 5);
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

function renderReportCard(title, canvasId, desc = '') {
    return `
    <div class="report-card">
        <div class="report-card-title">${title}</div>
        ${desc ? `<div style="font-size: 11px; color: var(--text-2); margin-top: -8px; margin-bottom: 12px; line-height: 1.4">${desc}</div>` : ''}
        <div class="mini-chart-container"><canvas id="${canvasId}"></canvas></div>
    </div>`;
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

    // Poblar Filtro de Equipos en SNC
    const teamFilter = document.getElementById('snc-team-filter');
    if (teamFilter) {
        const teams = [...new Set(gAthletesCache.map(a => a.team).filter(Boolean))].sort();
        teamFilter.innerHTML = '<option value="">Todas las plantillas</option>' + teams.map(t => `<option value="${t}" ${t === gSncTeamFilter ? 'selected' : ''}>${t}</option>`).join('');
    }
}

function filterAthletesSNC() {
    gSncTeamFilter = document.getElementById('snc-team-filter').value;
    renderSncTable();
}

async function deleteAthlete(id) { 
    if (!confirm("¿Eliminar deportista y todo su historial de evaluaciones? Esta acción no se puede deshacer.")) return; 
    
    try {
        const batch = db.batch();
        // Eliminar perfil
        batch.delete(db.collection('athletes').doc(id));
        
        // Eliminar historial vinculado (buscando por string y por número para seguridad)
        const q1 = await db.collection('Daily_Performance').where('athleteId', '==', id).get();
        q1.forEach(doc => batch.delete(doc.ref));
        
        const idNum = parseInt(id);
        if (!isNaN(idNum)) {
            const q2 = await db.collection('Daily_Performance').where('athleteId', '==', idNum).get();
            q2.forEach(doc => batch.delete(doc.ref));
        }

        await batch.commit();
        console.log("Atleta y registros eliminados con éxito.");
    } catch (err) {
        console.error("Error en eliminación completa:", err);
        // Fallback: eliminar solo el perfil si el historial falla
        db.collection('athletes').doc(id).delete();
    }
}

async function saveSettings() {
    const valIri = document.getElementById('threshold-iri').value;
    const valLapses = document.getElementById('threshold-lapses').value;
    const valIriOpt = document.getElementById('threshold-iri-opt').value;

    if (valIri !== "") THRESH.iriCritical = Number(valIri);
    if (valLapses !== "") THRESH.lapses = Number(valLapses);
    if (valIriOpt !== "") THRESH.iriOptimal = Number(valIriOpt);
    
    // 1. Forzar persistencia inmediata
    localStorage.setItem('imed_predictor_settings', JSON.stringify(THRESH));
    
    // 2. Sincronizar con el sistema (Firestore)
    try {
        await db.collection('system_config').doc('thresholds').set({
            ...THRESH,
            lastUpdated: firebase.firestore.FieldValue.serverTimestamp()
        });
        console.log("IMED: Ajustes guardados en la nube.");
    } catch (e) { 
        console.error("IMED: Error de persistencia en nube:", e);
    }
    
    renderDashboard();
    renderSncTable();
    renderAthletesTable();
    
    alert("Ajustes guardados correctamente en el sistema.");
}

function refreshData() { location.reload(); }

document.addEventListener('DOMContentLoaded', () => {
    document.documentElement.style.setProperty('overflow-y', 'auto', 'important');
    document.body.style.setProperty('overflow-y', 'auto', 'important');
    const dateEl = document.getElementById('live-date');
    if (dateEl) dateEl.textContent = new Date().toLocaleDateString('es-CL', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
});

// Cerrar modales al hacer clic fuera del modal-box (en el overlay)
window.addEventListener('click', (e) => {
    const athleteModal = document.getElementById('athlete-modal');
    const profileModal = document.getElementById('athlete-profile-modal');
    const sncModal = document.getElementById('snc-modal');
    
    if (e.target === athleteModal) {
        athleteModal.classList.add('hidden');
    }
    if (e.target === profileModal) {
        profileModal.classList.add('hidden');
    }
    if (e.target === sncModal) {
        sncModal.classList.add('hidden');
    }
});
