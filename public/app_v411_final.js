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
                <td>${p ? Math.round(p.iri) : '—'}</td>
                <td><span class="risk-badge ${snc.badgeClass}">${snc.label}</span></td>
                <td><span class="risk-badge ${latDev.class}">${latDev.label}</span></td>
                <td><span class="risk-badge ${tendency.class}">${tendency.label}</span></td>
                <td>${p ? p.date : '—'}</td>
                <td>${p?.timestamp ? (p.timestamp.seconds ? new Date(p.timestamp.seconds*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}) : '—') : '—'}</td>
                <td><span class="badge badge-gray" style="background:rgba(0,229,255,0.1); color:#00E5FF">${sessionCount}</span></td>
                <td><span class="risk-badge ${isDone ? 'badge-green' : 'badge-gray'}">${isDone ? 'SI' : 'NO'}</span></td>
                <td><button class="btn-mini">Análisis</button></td>
                <td style="display:flex; gap:5px; align-items:center">
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
                                    <td><span class="badge ${status.badgeClass}">${status.label}</span></td>
                                    <td>${lastEval ? lastEval.date : '—'}</td>
                                    <td>${lastEval ? `IRI: ${Math.round(lastEval.iri)}` : 'Pendiente'}</td>
                                    <td><button class="btn-mini">Ficha Completa</button></td>
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
            <p style="font-size:13px; color:var(--text-2); line-height:1.5">${a.notes || 'No hay notas técnicas registradas para este atleta. Utilice este espacio para documentar observaciones de campo o recomendaciones clínicas.'}</p>
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
    
    const records = allPerformance.filter(p => String(p.athleteId).trim() === String(id).trim());
    const latest = records[0] || {};
    const avgIri = records.length ? Math.round(records.reduce((acc, p) => acc + (p.iri || 0), 0) / records.length) : '—';
    const totalEvals = records.length;

    const element = document.createElement('div');
    element.style.padding = '40px';
    element.style.background = '#0a0c0f';
    element.style.color = '#ffffff';
    element.style.fontFamily = 'Inter, sans-serif';
    
    // Preparar tabla de historia (últimos 5)
    const historyRows = records.slice(0, 5).map(r => `
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05)">
            <td style="padding:10px 0; font-size:11px">${r.date}</td>
            <td style="padding:10px 0; font-size:11px; color:#32D74B; font-weight:bold">${Math.round(r.iri)}%</td>
            <td style="padding:10px 0; font-size:11px">${r.pvt?.metrics?.meanLatency ?? r.avg_reaction ?? '—'}ms</td>
            <td style="padding:10px 0; font-size:11px">${r.wellness?.sleepHours ?? '—'}h</td>
            <td style="padding:10px 0; font-size:11px">${r.wellness?.stressLevel ?? '—'}/5</td>
        </tr>
    `).join('');

    element.innerHTML = `
        <div style="border-bottom: 2px solid #00E5FF; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center">
            <div>
                <h1 style="margin:0; font-size: 24px; color: #00E5FF">IMED PREDICTOR — REPORTE ÉLITE</h1>
                <p style="margin:5px 0 0; font-size: 11px; color: #636375; letter-spacing:1px">NEURO-MECHANICAL VULNERABILITY INDEX (IVN)</p>
            </div>
            <div style="text-align: right">
                <p style="margin:0; font-size: 16px; font-weight: 800">${a.fullName.toUpperCase()}</p>
                <p style="margin:5px 0 0; font-size: 10px; color: #636375">FECHA: ${new Date().toLocaleDateString('es-CL')}</p>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 30px">
            <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); text-align:center">
                <div style="font-size:9px; color:#636375; margin-bottom:5px">ESTADO ACTUAL</div>
                <div style="font-size:16px; font-weight:bold; color:#00E5FF">${latest.iri ? Math.round(latest.iri)+'%' : 'PENDIENTE'}</div>
            </div>
            <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); text-align:center">
                <div style="font-size:9px; color:#636375; margin-bottom:5px">PROM. HISTÓRICO</div>
                <div style="font-size:16px; font-weight:bold; color:#32D74B">${avgIri}%</div>
            </div>
            <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); text-align:center">
                <div style="font-size:9px; color:#636375; margin-bottom:5px">SESIONES TOTALES</div>
                <div style="font-size:16px; font-weight:bold; color:#BF5AF2">${totalEvals}</div>
            </div>
        </div>

        <div style="margin-bottom: 30px">
            <h3 style="font-size: 12px; color:#00E5FF; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; margin-bottom:15px">ÚLTIMAS EVALUACIONES (DETALLE)</h3>
            <table style="width:100%; border-collapse: collapse; text-align:left">
                <thead>
                    <tr style="color:#636375; font-size:9px; text-transform:uppercase">
                        <th style="padding-bottom:10px">Fecha</th>
                        <th style="padding-bottom:10px">Índice IRI</th>
                        <th style="padding-bottom:10px">Latencia</th>
                        <th style="padding-bottom:10px">Sueño</th>
                        <th style="padding-bottom:10px">Estrés</th>
                    </tr>
                </thead>
                <tbody>${historyRows}</tbody>
            </table>
        </div>

        <div style="margin-bottom: 30px">
            <h3 style="font-size: 12px; color:#00E5FF; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; margin-bottom:10px">OBSERVACIONES TÉCNICAS</h3>
            <div style="background: rgba(255,255,255,0.02); padding: 20px; border-radius: 10px; font-size: 12px; line-height: 1.6; color: #8a8a9e; border: 1px solid rgba(255,255,255,0.03)">
                ${a.notes || 'El atleta mantiene una progresión estable. Se recomienda monitorear la carga mecánica en relación a la variabilidad de la latencia observada en las últimas 48 horas.'}
            </div>
        </div>

        <div style="margin-top: 40px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 20px; display:flex; justify-content:space-between; align-items:center">
            <div style="font-size: 9px; color: #444452">ID_SNC: ${id}</div>
            <div style="font-size: 9px; color: #636375; text-align:right">© 2026 IMED PREDICTOR — TECNOLOGÍA NEURO-MECÁNICA</div>
        </div>
    `;

    const opt = {
        margin: 0.5,
        filename: `Informe_Evolutivo_${a.fullName.replace(/\\s+/g, '_')}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, backgroundColor: '#0a0c0f', useCORS: true },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save();
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
