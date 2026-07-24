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
let allPerformanceRaw = [];
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
    db   = firebase.firestore();
    auth = firebase.auth();

    auth.onAuthStateChanged(async function(user) {
        if (user && !window._imedAppInitialized) {
            // Leer claims del token para obtener el rol
            try {
                const idTokenResult = await user.getIdTokenResult();
                window.currentUserRole = idTokenResult.claims.role || 'COACH';
                window.currentUserTeam = idTokenResult.claims.team || null;
                
                // Forzar roles oficiales por correo
                if (user.email === 'demo@imedpredictor.com') window.currentUserRole = 'DEMO';
                if (user.email === 'ps.patriciorubilar@gmail.com') window.currentUserRole = 'SUPER_ADMIN';
                
                // Resolver el tenantId del usuario
                let tenantId = idTokenResult.claims.tenantId || null;
                if (!tenantId) {
                    if (window.currentUserRole === 'DEMO') {
                        tenantId = 'demo_tenant';
                    } else if (window.currentUserRole !== 'SUPER_ADMIN') {
                        const tenantSnap = await db.collection('tenants').where('admin_email', '==', user.email).get();
                        if (!tenantSnap.empty) {
                            tenantId = tenantSnap.docs[0].id;
                        }
                    }
                }
                window.currentUserTenantId = tenantId;
                
                applyRolePermissions();
            } catch (err) {
                console.error("Error reading role:", err);
                window.currentUserRole = 'COACH';
                window.currentUserTenantId = null;
            }
            
            window._imedAppInitialized = true;
            init();
        }
    });
} catch (e) { console.error("Firebase Init Error:", e); }
 
function applyRolePermissions() {
    const role = window.currentUserRole;
    console.log("IMED: User Role detected ->", role);
    
    const navUsers = document.getElementById('nav-users');
    const navSaas = document.getElementById('nav-saas');
    const navBilling = document.getElementById('nav-billing');
    const navSettings = document.getElementById('nav-settings');

    if (role === 'DEMO') {
        // La cuenta demo tiene límites estrictos para capital semilla
        if (navUsers) navUsers.style.display = 'none';
        if (navSaas) navSaas.style.display = 'none';
        if (navBilling) navBilling.style.display = 'none';
        if (navSettings) navSettings.style.display = 'none';
    } else if (role === 'SUPER_ADMIN') {
        // El Super Admin tiene acceso completo a todos los privilegios
        if (navUsers) navUsers.style.display = '';
        if (navSaas) navSaas.style.display = '';
        if (navBilling) navBilling.style.display = '';
        if (navSettings) navSettings.style.display = '';
    } else if (role === 'PSICOLOGO' || role === 'COACH') {
        // El cliente de suscripción ve su panel, deportistas, ajustes y pagos, pero no administración SaaS
        if (navUsers) navUsers.style.display = 'none';
        if (navSaas) navSaas.style.display = 'none';
        if (navBilling) navBilling.style.display = '';
        if (navSettings) navSettings.style.display = '';
    } else {
        // Desloguear cualquier otra cuenta no autorizada
        auth.signOut();
        alert("Acceso no autorizado.");
    }
}

async function loadAssociationCode() {
    const user = firebase.auth().currentUser;
    if (!user) return;
    
    const codeEl = document.getElementById('settings-association-code');
    if (!codeEl) return;
    
    if (window.currentUserRole === 'SUPER_ADMIN') {
        codeEl.textContent = 'IMED-SUPER-ADMIN-GLOBAL';
        return;
    }
    
    try {
        const snap = await db.collection('tenants').where('admin_email', '==', user.email).get();
        if (!snap.empty) {
            const tenantData = snap.docs[0].data();
            codeEl.textContent = tenantData.associationCode || 'IMED-MOCKCODE';
        } else {
            codeEl.textContent = 'IMED-DEMO-2026';
        }
    } catch (e) {
        console.error("Error loading association code:", e);
        codeEl.textContent = 'IMED-DEMO-2026';
    }
}

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
    loadAssociationCode();
}

// ─── Onboarding & Real-time ───
function startAthletesOnboarding() {
    let query = db.collection('athletes');
    if (window.currentUserRole !== 'SUPER_ADMIN' && window.currentUserTenantId) {
        query = query.where('tenantId', '==', window.currentUserTenantId);
    } else if (window.currentUserTeam && window.currentUserRole !== 'ADMIN') {
        query = query.where('team', '==', window.currentUserTeam);
    }
    query.onSnapshot(snap => {
        gAthletesCache = snap.docs.map(d => {
            const data = d.data();
            return { id: d.id, ...data, fullName: data.fullName || `${data.firstName || ''} ${data.lastName || ''}`.trim() || d.id };
        });
        applyTeamFilterToPerformance();
        renderAthletesTable();
        renderSncTable();
        renderDashboard();
        populateAthleteSelects();
    }, err => {
        // Error handler: evita que el spinner quede atascado indefinidamente
        console.error('[ATHLETES LISTENER ERROR]', err);
        // Resetear a lista vacía para que la UI no quede bloqueada
        gAthletesCache = [];
        renderDashboard();
        // Mostrar mensaje de error en el panel de semáforo si existe
        const loadingEl = document.querySelector('.loading-athletes');
        if (loadingEl) {
            loadingEl.innerHTML = `<span style="color:#FF453A">⚠ Error al cargar atletas (${err.code || err.message}). Recarga la página.</span>`;
        }
    });
}

function startRealtimeListener() {
    if (unsubscribe) unsubscribe();
    const rtDot = document.getElementById('rt-dot');
    let query = db.collection('Daily_Performance');
    if (window.currentUserRole !== 'SUPER_ADMIN' && window.currentUserTenantId) {
        query = query.where('tenantId', '==', window.currentUserTenantId);
    }
    unsubscribe = query
        .orderBy('timestamp', 'desc')
        .limit(500)  // Aumentado: soporta equipos grandes con historial extendido
        .onSnapshot(snap => {
            // Filtrar IDs basura generados por el bug de race condition (athlete_pending_xxx)
            // Estos registros nunca corresponden a un atleta real del sistema
            allPerformanceRaw = snap.docs
                .map(d => ({ id: d.id, ...d.data() }))
                .filter(p => {
                    const aid = String(p.athleteId || '');
                    return aid.length > 0 && !aid.startsWith('athlete_pending_');
                });
            
            applyTeamFilterToPerformance();
            
            if (rtDot) { rtDot.className = 'status-dot green'; }
            renderDashboard();
            renderSncTable();
            renderAthletesTable();
        }, err => {
            console.error('[LISTENER ERROR]', err);
            if (rtDot) { rtDot.className = 'status-dot red'; }
        });
}

function applyTeamFilterToPerformance() {
    if (window.currentUserTeam && window.currentUserRole !== 'ADMIN') {
        const allowedIds = new Set(gAthletesCache.map(a => String(a.id)));
        allPerformance = allPerformanceRaw.filter(p => allowedIds.has(String(p.athleteId)));
    } else {
        allPerformance = allPerformanceRaw;
    }
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
        'settings': 'Configuración del Sistema',
        'users': 'Gestión de Accesos y Roles',
        'saas': 'SaaS Control de Inquilinos',
        'billing': 'Planes de Suscripción y Facturación'
    };
    const titleEl = document.getElementById('page-title');
    if (titleEl) titleEl.textContent = titleMap[viewId] || 'IMED Predictor';
    if (viewId === 'reports') loadAthleteReport(document.getElementById('report-athlete-select')?.value);
    if (viewId === 'users') loadDashboardUsers();
    if (viewId === 'saas') loadSaasTenants();
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
    // soreness eliminado del protocolo (no se recoge en esta versión)

    // Pesos basados en literatura de ciencias del deporte:
    //   sleepHours   30 pts — mayor predictor cognitivo (Watson et al., 2015)
    //   sleepQuality 25 pts — calidad sueño (Lastella et al., 2020)
    //   stressLevel  25 pts — predictor primario bienestar (Hooper & Mackinnon, 1995)
    //   fatigueLevel 20 pts — marcador complementario (Saw et al., 2016)
    // DEBE SER IDÉNTICA a pvt_exgauss_worker.py y snc_engine.dart
    const hScore = (Math.min(8, h) / 8) * 30;  // 30 pts
    const qScore = (q / 5) * 25;               // 25 pts
    const sScore = ((6 - s) / 5) * 25;         // 25 pts (inv.)
    const fScore = ((6 - f) / 5) * 20;         // 20 pts (inv.)
    return Math.round(hScore + qScore + sScore + fScore);
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
    // Si no hay wellness, se usa el PVT como base única. Si ya está calculado en p.iri, se respeta ese valor.
    const wellness = wellnessRaw !== null ? wellnessRaw : pvtRaw;
    const iriFinal = p.iri != null ? Number(p.iri) : Math.round((pvtRaw + wellness) / 2);
    
    // El NA (Neural Availability) se ve afectado por los lapsos (penalización técnica)
    const na = Math.max(0, iriFinal * (1 - (lapses * 0.1)));
    
    const gps = p.gps || {};
    const decel = gps.decel_high || gps.decel_z5 || 0;
    const sprint = (gps.sprint_dist || gps.sprint_distance || 0) / 10;
    const load = (decel * 0.6) + (sprint * 0.4);
    
    const acwr = p.acwr || 1.0;
    const ivn = na > 0 ? ((load * acwr) / (na / 100)) : load;

    let level = 'GREEN', label = 'ÓPTIMO';
    
    // Motor PIFC: Usar el estado Ex-Gaussiano si el backend lo calculó
    const aa = p.advanced_analysis || (p.pvt && p.pvt.advanced_analysis);
    if (aa && aa.readiness_status) {
        level = aa.readiness_status;
        label = aa.fatigue_label || level.toUpperCase();
    } else {
        // Fallback heredado (Sin Z-scores)
        const critIri = THRESH.iriCritical || 60;
        const optIri = THRESH.iriOptimal || 85;
        const maxLapses = THRESH.lapses || 2;

        if (iriFinal < critIri || lapses >= maxLapses || ivn > 30) { 
            level = 'RED'; label = 'RIESGO CRÍTICO'; 
        }
        else if (iriFinal < optIri || ivn > 25) { 
            level = 'YELLOW'; label = 'ADVERTENCIA'; 
        }
    }

    // Derivar badge/ring class para 4 estados PIFC
    const levelLower = level.toLowerCase();
    return { 
        level, label, na, wellness, ivn, iri: iriFinal,
        badgeClass: `badge-${levelLower}`, 
        ringClass:  `ring-${levelLower}`,
        action: p.action || '',
        pifc_protocol: aa && aa.pifc_protocol ? aa.pifc_protocol : null
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
        if (!aid) return;
        // Conservar el registro con la fecha MÁS RECIENTE por atleta
        if (!latest[aid] || (p.date || '') > (latest[aid].date || '')) {
            latest[aid] = p;
        }
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
        const isToday = p.date === today;
        const safeName = (p.athleteName || p.athleteId || '').replace(/'/g, "\\'");
        return `
            <div class="athlete-card" onclick="openSncModal('${p.athleteId}')" style="position:relative">
                <div class="athlete-avatar">${initials}<div class="risk-ring ${ivn.ringClass}"></div></div>
                <div class="athlete-info">
                    <div class="athlete-name">${p.athleteName || p.athleteId}</div>
                    <div class="athlete-pos" style="color: ${isToday ? 'var(--text-2)' : '#FF9F0A'}; font-size: 0.75rem;">
                        📅 ${p.date ? p.date.split('-').reverse().join('-') : '—'}${isToday ? '' : ' · <strong>DATO ANTERIOR</strong>'}
                    </div>
                </div>
                <div class="athlete-metrics">
                    <div class="metric-mini"><div class="val">${Math.round(p.iri)}</div><div class="lbl">IRI</div></div>
                    <div class="metric-mini"><div class="val">${p.pvt?.metrics?.lapses ?? p.lapses ?? 0}</div><div class="lbl">LAPSES</div></div>
                    <div class="metric-mini">
                        <div class="val" style="color:${hasGps ? 'var(--blue)' : '#636375'}">${hasGps ? ivn.ivn.toFixed(1)+'x' : 'S/D'}</div>
                        <div class="lbl">${hasGps ? 'INDICE IVN' : 'SIN GPS'}</div>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap">
                    <span class="risk-badge ${ivn.badgeClass}">${ivn.label}</span>
                    ${!isToday ? `<button class="btn-mini" style="background:rgba(255,214,10,0.1);border:1px solid rgba(255,214,10,0.3);color:#FFD60A;font-size:10px;padding:3px 8px;" onclick="event.stopPropagation(); openManualEntry('${p.athleteId}','${safeName}','${today}')">+ Registrar Hoy</button>` : ''}
                    <button class="btn-delete" style="width:28px; height:28px; padding:0; display:flex; align-items:center; justify-content:center; border-radius:6px; background:rgba(255,69,58,0.1); border:1px solid rgba(255,69,58,0.2); color:#FF453A" onclick="event.stopPropagation(); deleteAthlete('${p.athleteId}')">🗑</button>
                </div>
            </div>`;
    }).join('') : '<div class="empty-state">No hay evaluaciones registradas hoy.</div>';

    // ── Atletas sin datos de hoy → mostrar sección de pendientes ────────────
    const athleteIdsWithData = new Set(displayList.map(p => String(p.athleteId)));
    const pending = gAthletesCache.filter(a => !athleteIdsWithData.has(String(a.id)));
    if (pending.length > 0) {
        const pendingHtml = pending.map(a => {
            const safeName = (a.fullName || a.id).replace(/'/g, "\\'");
            const initials = (a.fullName || 'AT').split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase();
            return `
            <div class="athlete-card" style="opacity:0.55; border:1px dashed var(--border)">
                <div class="athlete-avatar" style="background:rgba(255,255,255,0.05)">${initials}</div>
                <div class="athlete-info">
                    <div class="athlete-name">${a.fullName || a.id}</div>
                    <div class="athlete-pos" style="color:#636375; font-size:0.75rem;">Sin evaluacion hoy</div>
                </div>
                <div class="athlete-metrics">
                    <div class="metric-mini"><div class="val" style="color:#636375">—</div><div class="lbl">IRI</div></div>
                    <div class="metric-mini"><div class="val" style="color:#636375">—</div><div class="lbl">LAPSES</div></div>
                    <div class="metric-mini"><div class="val" style="color:#636375">—</div><div class="lbl">IVN</div></div>
                </div>
                <button class="btn-mini" style="background:rgba(255,214,10,0.1);border:1px solid rgba(255,214,10,0.3);color:#FFD60A;font-size:11px;padding:4px 10px;" onclick="openManualEntry('${a.id}','${safeName}','${today}')">+ Registrar Manual</button>
            </div>`;
        }).join('');
        container.innerHTML += `
            <div style="width:100%;padding:12px 0 4px;font-size:10px;font-weight:700;letter-spacing:1px;color:#636375;text-transform:uppercase;">
                SIN EVALUACION HOY
            </div>
            ${pendingHtml}`;
    }
    
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
        // Ordenar por fecha REAL (campo 'date') desc para obtener el registro más reciente
        const sortedRecords = [...records].sort((a, b) => (b.date || '').localeCompare(a.date || ''));
        const p = sortedRecords[0]; // El más reciente por fecha, no por timestamp Firestore
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
    // Ordenar por fecha desc para asegurar que records[0] es el más reciente
    const sorted = [...records].sort((a, b) => (b.date || '').localeCompare(a.date || ''));
    const latest = sorted[0].iri || 0;
    const prev = sorted[1].iri || 0;
    const diff = latest - prev;
    if (diff > 5) return { label: 'MEJORA', class: 'badge-green' };
    if (diff < -5) return { label: 'CAÍDA', class: 'badge-red' };
    return { label: 'ESTABLE', class: 'badge-green' };
}

function calcLatencyDev(p, records) {
    if (!p || records.length < 3) return { label: 'NORMAL', class: 'badge-green' };
    const current = p.pvt?.metrics?.meanLatency ?? p.avg_reaction ?? 280;
    // Ordenar para asegurar que slice(1,10) son los registros anteriores reales
    const sorted = [...records].sort((a, b) => (b.date || '').localeCompare(a.date || ''));
    const history = sorted.slice(1, 10).map(r => r.pvt?.metrics?.meanLatency ?? r.avg_reaction ?? 280);
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

    // Obtener clinical record con valores por defecto
    const cr = a.clinical_record || {};
    const bloodType = cr.blood_type || '';
    const chronicPath = cr.chronic_pathologies || '';
    const allergies = cr.allergies || '';
    const medications = cr.medications || '';
    const surgeries = cr.surgeries || '';
    const lesions = cr.lesions_history || '';
    const antro = cr.antropometria || {};
    const wKg = antro.weight_kg || '';
    const hCm = antro.height_cm || '';
    const fatPct = antro.fat_percent || '';
    const musPct = antro.muscle_percent || '';
    
    document.getElementById('tab-container-ficha').innerHTML = `
        <!-- Tabs Header -->
        <div class="profile-tabs">
            <button class="profile-tab-btn active" id="tab-btn-performance" onclick="switchProfileTab('performance')">📊 Rendimiento</button>
            <button class="profile-tab-btn" id="tab-btn-clinical" onclick="switchProfileTab('clinical')">📋 Ficha Clínica</button>
        </div>

        <!-- Tab Content: Performance (Antes por defecto) -->
        <div class="profile-tab-content active" id="tab-content-performance">
            <div class="grid-2col" style="gap:15px">
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
        </div>

        <!-- Tab Content: Clinical Record [NUEVO] -->
        <div class="profile-tab-content" id="tab-content-clinical">
            <form id="clinical-record-form" onsubmit="saveClinicalRecord(event, '${a.id}')">
                <div class="clinical-grid">
                    
                    <!-- Sección Médica General -->
                    <div>
                        <div class="clinical-section-title">🏥 Antecedentes Médicos Generales</div>
                        <div class="clinical-field-group">
                            <label class="form-label">Grupo Sanguíneo</label>
                            <input type="text" id="cr-blood" class="input-glass w-full" placeholder="ej: O Rh+" value="${bloodType}" />
                        </div>
                        <div class="clinical-field-group">
                            <label class="form-label">Alergias Conocidas</label>
                            <input type="text" id="cr-allergies" class="input-glass w-full" placeholder="Alergias a medicamentos, alimentos, etc." value="${allergies}" />
                        </div>
                        <div class="clinical-field-group">
                            <label class="form-label">Patologías Crónicas</label>
                            <input type="text" id="cr-chronic" class="input-glass w-full" placeholder="ej: Asma, Diabetes, Hipertensión" value="${chronicPath}" />
                        </div>
                        <div class="clinical-field-group">
                            <label class="form-label">Medicamentos en Uso Permanente</label>
                            <input type="text" id="cr-meds" class="input-glass w-full" placeholder="Fármacos o suplementos recetados" value="${medications}" />
                        </div>
                    </div>

                    <!-- Sección Antropométrica -->
                    <div>
                        <div class="clinical-section-title">⚖️ Mediciones Antropométricas</div>
                        <div class="clinical-input-row" style="margin-bottom: 14px">
                            <div class="clinical-field-group">
                                <label class="form-label">Peso (kg)</label>
                                <input type="number" step="0.1" id="cr-weight" class="input-glass w-full" placeholder="ej: 76.5" value="${wKg}" />
                            </div>
                            <div class="clinical-field-group">
                                <label class="form-label">Estatura (cm)</label>
                                <input type="number" id="cr-height" class="input-glass w-full" placeholder="ej: 182" value="${hCm}" />
                            </div>
                        </div>
                        <div class="clinical-input-row">
                            <div class="clinical-field-group">
                                <label class="form-label">% Grasa Corporal</label>
                                <input type="number" step="0.1" id="cr-fat" class="input-glass w-full" placeholder="ej: 10.5" value="${fatPct}" />
                            </div>
                            <div class="clinical-field-group">
                                <label class="form-label">% Masa Muscular</label>
                                <input type="number" step="0.1" id="cr-muscle" class="input-glass w-full" placeholder="ej: 45.2" value="${musPct}" />
                            </div>
                        </div>
                    </div>

                    <!-- Historial Quirúrgico y Deportivo (Ancho completo) -->
                    <div class="clinical-grid-full">
                        <div class="clinical-section-title">🤕 Historial de Lesiones y Cirugías</div>
                        <div class="clinical-field-group">
                            <label class="form-label">Cirugías Previas</label>
                            <textarea id="cr-surgeries" class="input-glass w-full" rows="2" placeholder="Describa cirugías previas y año..." style="font-family: inherit; font-size: 13px; padding: 10px">${surgeries}</textarea>
                        </div>
                        <div class="clinical-field-group">
                            <label class="form-label">Historial de Lesiones Deportivas</label>
                            <textarea id="cr-lesions" class="input-glass w-full" rows="3" placeholder="ej: Esguince ligamento medial rodilla (2024), Desgarro isquiotibiales (2025)..." style="font-family: inherit; font-size: 13px; padding: 10px">${lesions}</textarea>
                        </div>
                    </div>

                </div>

                <button type="submit" class="btn-primary w-full" style="margin-top:20px; background: linear-gradient(135deg, var(--blue), #0077ff); border: none;">
                    💾 Guardar Ficha Clínica
                </button>
            </form>
        </div>
    `;
    document.getElementById('athlete-profile-modal').classList.remove('hidden');
}

// ─── Funciones Globales para las Pestañas y Guardado de Ficha Clínica ───
window.switchProfileTab = function(tabName) {
    document.querySelectorAll('.profile-tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.profile-tab-content').forEach(content => content.classList.remove('active'));

    if (tabName === 'performance') {
        document.getElementById('tab-btn-performance').classList.add('active');
        document.getElementById('tab-content-performance').classList.add('active');
    } else if (tabName === 'clinical') {
        document.getElementById('tab-btn-clinical').classList.add('active');
        document.getElementById('tab-content-clinical').classList.add('active');
    }
};

window.saveClinicalRecord = async function(event, athleteId) {
    event.preventDefault();
    const btn = event.submitter || event.target.querySelector('button[type="submit"]');
    const origText = btn.innerHTML;
    
    btn.disabled = true;
    btn.textContent = 'Guardando ficha...';

    const blood = document.getElementById('cr-blood').value.trim();
    const allergies = document.getElementById('cr-allergies').value.trim();
    const chronic = document.getElementById('cr-chronic').value.trim();
    const meds = document.getElementById('cr-meds').value.trim();
    const surgeries = document.getElementById('cr-surgeries').value.trim();
    const lesions = document.getElementById('cr-lesions').value.trim();

    const weight = parseFloat(document.getElementById('cr-weight').value) || null;
    const height = parseInt(document.getElementById('cr-height').value) || null;
    const fat = parseFloat(document.getElementById('cr-fat').value) || null;
    const muscle = parseFloat(document.getElementById('cr-muscle').value) || null;

    const clinical_record = {
        blood_type: blood,
        chronic_pathologies: chronic,
        allergies: allergies,
        medications: meds,
        surgeries: surgeries,
        lesions_history: lesions,
        antropometria: {
            weight_kg: weight,
            height_cm: height,
            fat_percent: fat,
            muscle_percent: muscle
        },
        last_updated: new Date().toISOString(),
        updated_by: firebase.auth().currentUser ? firebase.auth().currentUser.email : 'evaluador'
    };

    try {
        await db.collection('athletes').doc(athleteId).update({ clinical_record });
        
        // Actualizar el caché local
        const localAth = gAthletesCache.find(x => x.id === athleteId);
        if (localAth) {
            localAth.clinical_record = clinical_record;
        }

        showToast('success', 'Ficha Guardada', 'La ficha clínica del deportista ha sido actualizada.');
    } catch (err) {
        console.error("Error al guardar ficha clínica:", err);
        showToast('error', 'Error al Guardar', 'No se pudo guardar la ficha clínica en Firestore.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = origText;
    }
};


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
        const batch = db.batch();
        // 1. Eliminar perfil del atleta
        batch.delete(db.collection('athletes').doc(id));
        
        // 2. Eliminar registros de Daily_Performance asociados (nombre correcto de colección)
        const snapshot = await db.collection('Daily_Performance').where('athleteId', '==', id).get();
        snapshot.docs.forEach(doc => batch.delete(doc.ref));
        
        // 3. Eliminar también por si el ID fue guardado como número
        const idNum = parseInt(id);
        if (!isNaN(idNum)) {
            const snap2 = await db.collection('Daily_Performance').where('athleteId', '==', idNum).get();
            snap2.docs.forEach(doc => batch.delete(doc.ref));
        }

        await batch.commit();
        alert('Deportista eliminado correctamente.');
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
    // Buscar el registro con la fecha MÁS RECIENTE (campo 'date'), no el primero por timestamp de Firestore
    const athleteRecords = allPerformance.filter(x => String(x.athleteId).trim() === String(id).trim());
    const p = athleteRecords.sort((a, b) => (b.date || '').localeCompare(a.date || ''))[0];
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
        ${renderHistoricalDataTable(a.id)}
        <div class="prescription-box" style="margin-top:20px">
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
            <button class="btn-primary w-full" style="margin-top:16px; background:var(--blue-dim); color:var(--blue); border:1px solid var(--blue)" onclick="viewAthleteTrends('${a.id}')">📊 Ver Tendencias en Gráficos</button>
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
                      : aa.readiness_status === 'ORANGE' ? '#FF9500'
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

            ${aa.pifc_protocol ? `
            <div style="margin-top:12px; padding:12px; border-radius:8px; background:rgba(255,255,255,0.03); border:1px solid ${statusColor}44;">
                <div style="font-size:11px; font-weight:800; color:${statusColor}; letter-spacing:0.5px; margin-bottom:8px;">
                    PIFC: ${aa.pifc_protocol.title.toUpperCase()}
                </div>
                <ul style="margin:0; padding-left:16px; font-size:12px; color:var(--text-1); line-height:1.6;">
                    ${aa.pifc_protocol.interventions.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>` : ''}
        </div>
    </div>`;
}


function closeSncModal() { document.getElementById('snc-modal').classList.add('hidden'); }
function closeAthleteProfile() { document.getElementById('athlete-profile-modal').classList.add('hidden'); }

/**
 * ─── Tabla de Historial Ex-Gaussiano ───────────────────────────────────────────
 * Genera un panel con tabla completa de registros históricos por día:
 * Fecha | IRI | μ | σ | τ | τ Z-Score | Wellness | Wellness Z-Score | Estado
 */
function renderHistoricalDataTable(athleteId) {
    const records = allPerformance
        .filter(p => String(p.athleteId).trim() === String(athleteId).trim())
        .sort((a, b) => (b.date || '').localeCompare(a.date || ''));

    if (!records.length) return '';

    const rows = records.map(r => {
        const st = getUnifiedStatus(r);
        const aa = r.advanced_analysis || {};
        const mu      = aa.mu_ms    != null ? aa.mu_ms.toFixed(1)    : '—';
        const sigma   = aa.sigma_ms != null ? aa.sigma_ms.toFixed(1) : '—';
        const tau     = aa.tau_ms   != null ? aa.tau_ms.toFixed(1)   : '—';
        const tauZ    = aa.tau_zscore != null ? Number(aa.tau_zscore).toFixed(2) : '—';
        const wVal    = calculateWellness(r);
        const wellness = wVal != null ? wVal : '—';
        const wZ      = aa.wellness_zscore != null ? Number(aa.wellness_zscore).toFixed(2) : '—';
        const lapses  = r.pvt?.metrics?.lapses ?? r.lapses ?? '—';
        const latency = r.pvt?.metrics?.meanLatency ?? r.avg_reaction ?? '—';

        // Colores semáforo por fila — 4 estados PIFC
        const iriColor = st.level === 'RED'    ? '#FF4D4D'
                       : st.level === 'ORANGE' ? '#FF9500'
                       : st.level === 'YELLOW' ? '#FFD60A'
                       : '#32D74B';
        const tauZColor = tauZ !== '—'
            ? (Number(tauZ) > 1.5 ? '#FF4D4D' : Number(tauZ) > 1.0 ? '#FFD60A' : '#32D74B')
            : '#636375';
        const wZColor = wZ !== '—'
            ? (Number(wZ) < -1.2 ? '#FF4D4D' : Number(wZ) < -0.8 ? '#FFD60A' : '#32D74B')
            : '#636375';
        const wellnessColor = wellness !== '—'
            ? (wellness < 60 ? '#FF4D4D' : wellness < 75 ? '#FFD60A' : '#32D74B')
            : '#636375';

        // Badge de estado compacto — 4 niveles PIFC
        const stateBadgeStyle = st.level === 'RED'
            ? 'background:rgba(255,77,77,0.15);   color:#FF4D4D; border:1px solid rgba(255,77,77,0.3)'
            : st.level === 'ORANGE'
            ? 'background:rgba(255,149,0,0.15);  color:#FF9500; border:1px solid rgba(255,149,0,0.3)'
            : st.level === 'YELLOW'
            ? 'background:rgba(255,214,10,0.15); color:#FFD60A; border:1px solid rgba(255,214,10,0.3)'
            : st.level === 'GRAY'
            ? 'background:rgba(255,255,255,0.05); color:#636375; border:1px solid rgba(255,255,255,0.1)'
            : 'background:rgba(50,215,75,0.15);  color:#32D74B; border:1px solid rgba(50,215,75,0.3)';

        const dateFormatted = r.date ? r.date.split('-').reverse().join('/') : '—';

        return `
            <tr class="hist-row">
                <td class="hist-td mono-cell" style="color:#9A9AAF; white-space:nowrap">${dateFormatted}</td>
                <td class="hist-td" style="text-align:center">
                    <span style="font-size:13px; font-weight:800; color:${iriColor}">${Math.round(st.iri)}</span>
                </td>
                <td class="hist-td" style="text-align:center; color:#9A9AAF">${lapses}</td>
                <td class="hist-td" style="text-align:center">
                    <span style="font-size:12px; font-weight:700; color:#00E5FF">${mu !== '—' ? mu + '<span style="font-size:9px;opacity:0.6">ms</span>' : '—'}</span>
                </td>
                <td class="hist-td" style="text-align:center">
                    <span style="font-size:12px; font-weight:700; color:#FF9F0A">${sigma !== '—' ? sigma + '<span style="font-size:9px;opacity:0.6">ms</span>' : '—'}</span>
                </td>
                <td class="hist-td" style="text-align:center">
                    <span style="font-size:12px; font-weight:700; color:${tauZColor}">${tau !== '—' ? tau + '<span style="font-size:9px;opacity:0.6">ms</span>' : '—'}</span>
                </td>
                <td class="hist-td" style="text-align:center">
                    <span style="font-size:12px; font-weight:800; color:${tauZColor}">${tauZ}</span>
                </td>
                <td class="hist-td" style="text-align:center">
                    <span style="font-size:12px; font-weight:700; color:${wellnessColor}">${wellness !== '—' ? wellness + '<span style="font-size:9px;opacity:0.6">/100</span>' : '—'}</span>
                </td>
                <td class="hist-td" style="text-align:center">
                    <span style="font-size:12px; font-weight:800; color:${wZColor}">${wZ}</span>
                </td>
                <td class="hist-td" style="text-align:center">
                    <span style="font-size:9px; font-weight:700; padding:3px 8px; border-radius:99px; ${stateBadgeStyle}">${st.label}</span>
                </td>
            </tr>`;
    }).join('');

    return `
    <div class="hist-panel" style="margin-top:20px">
        <!-- Header -->
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px">
            <div>
                <div style="font-size:9px; font-weight:700; letter-spacing:2px; color:#636375; margin-bottom:4px">HISTORIAL COMPLETO</div>
                <div style="font-size:13px; font-weight:700; color:#fff">📋 Evolución Ex-Gaussiana por Día <span style="font-size:11px; color:#636375; font-weight:400">(${records.length} sesiones registradas)</span></div>
            </div>
            <div style="display:flex; gap:8px">
                <button onclick="exportHistoricalCSV('${athleteId}')"
                    style="padding:6px 14px; background:rgba(0,229,255,0.1); border:1px solid rgba(0,229,255,0.25); color:#00E5FF;
                           border-radius:8px; font-size:10px; font-weight:700; cursor:pointer; letter-spacing:0.5px; font-family:var(--font)">
                    ⬇ CSV
                </button>
            </div>
        </div>

        <!-- Leyenda de columnas clave -->
        <div style="display:flex; gap:16px; margin-bottom:12px; flex-wrap:wrap">
            <div style="font-size:10px; color:#636375"><span style="color:#00E5FF; font-weight:700">μ</span> Velocidad Motora</div>
            <div style="font-size:10px; color:#636375"><span style="color:#FF9F0A; font-weight:700">σ</span> Consistencia</div>
            <div style="font-size:10px; color:#636375"><span style="color:#BF5AF2; font-weight:700">τ</span> Fatiga Central</div>
            <div style="font-size:10px; color:#636375"><span style="color:#32D74B; font-weight:700">Z</span> = desviación vs. media personal 21d</div>
        </div>

        <!-- Tabla scrollable -->
        <div style="overflow-x:auto; border-radius:10px; border:1px solid rgba(255,255,255,0.06); background:rgba(0,0,0,0.2)">
            <table style="width:100%; border-collapse:collapse; min-width:760px">
                <thead>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.08)">
                        <th class="hist-th">FECHA</th>
                        <th class="hist-th" style="text-align:center">IRI</th>
                        <th class="hist-th" style="text-align:center">LAPSES</th>
                        <th class="hist-th" style="text-align:center; color:#00E5FF">μ (ms)</th>
                        <th class="hist-th" style="text-align:center; color:#FF9F0A">σ (ms)</th>
                        <th class="hist-th" style="text-align:center; color:#BF5AF2">τ (ms)</th>
                        <th class="hist-th" style="text-align:center; color:#BF5AF2">τ Z-Score</th>
                        <th class="hist-th" style="text-align:center; color:#32D74B">WELLNESS</th>
                        <th class="hist-th" style="text-align:center; color:#32D74B">W. Z-Score</th>
                        <th class="hist-th" style="text-align:center">ESTADO</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>

        <!-- Nota técnica -->
        <div style="margin-top:10px; font-size:10px; color:#636375; font-style:italic; line-height:1.5">
            * Z-Scores calculados sobre ventana móvil de 21 días. Valores τ Z > 1.5 = alerta fatiga SNC. Wellness Z < −1.2 = alerta recuperación insuficiente.
        </div>
    </div>`;
}

/**
 * Exporta el historial del atleta como archivo CSV
 */
function exportHistoricalCSV(athleteId) {
    const a = gAthletesCache.find(x => x.id === athleteId);
    const records = allPerformance
        .filter(p => String(p.athleteId).trim() === String(athleteId).trim())
        .sort((a, b) => (b.date || '').localeCompare(a.date || ''));

    if (!records.length) return alert('No hay datos históricos para exportar.');

    const headers = ['Fecha','IRI','Lapses','Latencia Media (ms)','μ (ms)','σ (ms)','τ (ms)','τ Z-Score','Wellness (/100)','Wellness Z-Score','Estado'];
    const csvRows = [headers.join(',')];

    records.forEach(r => {
        const st  = getUnifiedStatus(r);
        const aa  = r.advanced_analysis || {};
        const row = [
            r.date || '',
            Math.round(st.iri),
            r.pvt?.metrics?.lapses ?? r.lapses ?? '',
            r.pvt?.metrics?.meanLatency ?? r.avg_reaction ?? '',
            aa.mu_ms    != null ? aa.mu_ms.toFixed(1)    : '',
            aa.sigma_ms != null ? aa.sigma_ms.toFixed(1) : '',
            aa.tau_ms   != null ? aa.tau_ms.toFixed(1)   : '',
            aa.tau_zscore      != null ? Number(aa.tau_zscore).toFixed(3)      : '',
            calculateWellness(r) != null ? calculateWellness(r) : '',
            aa.wellness_zscore  != null ? Number(aa.wellness_zscore).toFixed(3) : '',
            st.label
        ];
        csvRows.push(row.join(','));
    });

    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `IMED_Historial_${(a?.fullName || athleteId).replace(/\s+/g, '_')}.csv`;
    link.click();
    URL.revokeObjectURL(url);
}

function showToast(type, title, sub) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.innerHTML = `<div class="toast-icon">${type === 'success' ? '✓' : '⚠'}</div><div class="toast-text"><div class="toast-title">${title}</div><div class="toast-sub">${sub}</div></div>`;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 4000);
}

// ─── Trends & Reports ───
function loadAthleteReport(athleteId) {
    const container = document.getElementById('report-container');
    const advancedContainer = document.getElementById('advanced-report-container');
    if (!athleteId) { 
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">📊</div><p>Selecciona un atleta</p></div>'; 
        advancedContainer.innerHTML = '';
        return; 
    }
    let records = allPerformance.filter(p => String(p.athleteId).trim() === String(athleteId).trim());
    // Ordenar por fecha real (campo 'date') de forma ascendente para que el gráfico
    // muestre la cronología correcta, independientemente del timestamp de Firestore.
    records.sort((a, b) => {
        const da = a.date || (a.id ? a.id.split('_').slice(1).join('_') : '') || '';
        const db2 = b.date || (b.id ? b.id.split('_').slice(1).join('_') : '') || '';
        return da.localeCompare(db2);
    });
    records = records.slice(-14); // Últimos 14 días en orden cronológico
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

    // ── Gráficos Avanzados y Tabla Histórica en la sección de Reportes ──
    advancedContainer.innerHTML = `
        <div class="report-card" style="border-left:3px solid #00E5FF; margin-top:20px; display:flex; flex-direction:column; gap:20px;">
            <div class="report-card-title" style="color:#00E5FF">📈 GRÁFICO DE TENDENCIAS CRUZADAS (14D) — Z-SCORE VS WELLNESS</div>
            <div style="height:300px; width:100%; position:relative;">
                <canvas id="athlete-trend-chart"></canvas>
            </div>
        </div>

        <div class="report-card" style="border-left:3px solid #FF9F0A; margin-top:20px; display:flex; flex-direction:column; gap:20px;">
            <div class="report-card-title" style="color:#FF9F0A">🎯 SCATTER PLOT — 30 ENSAYOS PVT-B (SESIÓN MÁS RECIENTE)</div>
            <div style="height:300px; width:100%; position:relative;">
                <canvas id="athlete-trials-chart"></canvas>
            </div>
        </div>

        <div class="report-card" style="border-left:3px solid #BF5AF2; margin-top:20px">
            <div class="report-card-title" style="color:#BF5AF2">📋 TABLA HISTÓRICA COMPLETA — ANÁLISIS EX-GAUSSIANO + WELLNESS</div>
            <p style="font-size:12px; color:var(--text-2); margin-bottom:16px; line-height:1.5">
                Historial completo de sesiones con todos los biomarcadores: μ (velocidad motora), σ (consistencia), τ (fatiga central),
                Z-scores de τ y Wellness — ordenados del más reciente al más antiguo.
                Puedes exportar todos los datos en formato CSV haciendo click en el botón CSV.
            </p>
            ${renderHistoricalDataTable(athleteId)}
        </div>`;

    renderAthleteTrendChart(records);
    renderAthleteTrialsChart(records[records.length - 1]);
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

function renderAthleteTrendChart(records) {
    const labels = records.map(p => p.date || '');
    const tauZ = records.map(p => p.advanced_analysis?.tau_zscore ?? null);
    const wellnessZ = records.map(p => p.advanced_analysis?.wellness_zscore ?? null);

    reportCharts.push(new Chart(document.getElementById('athlete-trend-chart'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'τ Z-Score (Fatiga Central)',
                    data: tauZ,
                    borderColor: '#FF4D4D',
                    backgroundColor: 'transparent',
                    yAxisID: 'y',
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 4
                },
                {
                    label: 'Wellness Z-Score',
                    data: wellnessZ,
                    borderColor: '#32D74B',
                    backgroundColor: 'transparent',
                    yAxisID: 'y1',
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: true, labels: { color: '#636375' } } },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#636375' } },
                y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'τ Z-Score (Deviación estándar)', color: '#636375' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#636375' } },
                y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'Wellness Z-Score', color: '#636375' }, grid: { drawOnChartArea: false }, ticks: { color: '#636375' } }
            }
        }
    }));
}

function renderAthleteTrialsChart(latestRecord) {
    const canvas = document.getElementById('athlete-trials-chart');
    if (!latestRecord || !latestRecord.pvt || !latestRecord.pvt.trials || !latestRecord.pvt.trials.length) {
        canvas.parentElement.innerHTML = '<div class="empty-state" style="height:100%"><p>No hay datos de ensayos brutos (trials) para la última sesión.</p></div>';
        return;
    }
    const trials = latestRecord.pvt.trials;
    const data = trials.map((val, idx) => ({ x: idx + 1, y: val }));

    reportCharts.push(new Chart(canvas, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Tiempo de Reacción (ms)',
                data: data,
                backgroundColor: '#FF9F0A',
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { 
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(ctx) { return `Ensayo \${ctx.raw.x}: \${ctx.raw.y} ms`; }
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Nº de Ensayo (1-30)', color: '#636375', font: { weight: 'bold' } }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#636375', stepSize: 5 } },
                y: { title: { display: true, text: 'Latencia (ms)', color: '#636375', font: { weight: 'bold' } }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#636375' } }
            }
        }
    }));
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

// ─── Registro Manual de Evaluacion ───────────────────────────────────────────
// Permite al entrenador ingresar resultados desde el dashboard cuando
// la app movil no sincronizo los datos del deportista.

function openManualEntry(athleteId, athleteName, date) {
    const modal = document.getElementById('manual-entry-modal');
    document.getElementById('manual-athlete-id').value    = athleteId;
    document.getElementById('manual-athlete-title').textContent = `Registrar: ${athleteName}`;
    document.getElementById('manual-date-picker').value  = date || new Date().toLocaleDateString('en-CA');
    // Limpiar campos
    ['manual-iri','manual-lapses','manual-latency','manual-sleep',
     'manual-sleep-q','manual-stress','manual-fatigue'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    const errEl = document.getElementById('manual-entry-error');
    if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; }
    modal.classList.remove('hidden');
}

function closeManualEntry(e) {
    if (!e || e.target.id === 'manual-entry-modal') {
        document.getElementById('manual-entry-modal').classList.add('hidden');
    }
}

async function submitManualEntry() {
    const athleteId   = document.getElementById('manual-athlete-id').value;
    const date        = document.getElementById('manual-date-picker').value;
    const iri         = parseInt(document.getElementById('manual-iri').value);
    const lapses      = parseInt(document.getElementById('manual-lapses').value || '0');
    const meanLatency = parseInt(document.getElementById('manual-latency').value || '0');
    const sleepHours  = parseFloat(document.getElementById('manual-sleep').value || '0') || null;
    const sleepQuality= parseInt(document.getElementById('manual-sleep-q').value || '0') || null;
    const stressLevel = parseInt(document.getElementById('manual-stress').value || '0') || null;
    const fatigueLevel= parseInt(document.getElementById('manual-fatigue').value || '0') || null;

    const errEl = document.getElementById('manual-entry-error');

    if (!athleteId || !date) {
        errEl.textContent = 'Error interno: atleta o fecha no identificados.';
        errEl.style.display = 'block';
        return;
    }
    if (isNaN(iri) || iri < 0 || iri > 100) {
        errEl.textContent = 'El IRI debe ser un numero entre 0 y 100.';
        errEl.style.display = 'block';
        return;
    }

    const btn = document.getElementById('btn-manual-submit');
    btn.disabled = true;
    btn.textContent = 'Registrando...';
    errEl.style.display = 'none';

    try {
        const fn = firebase.functions().httpsCallable('manual_register');
        const res = await fn({
            athleteId, date, iri, lapses, meanLatency,
            sleepHours, sleepQuality, stressLevel, fatigueLevel
        });

        if (res.data.status === 'success') {
            document.getElementById('manual-entry-modal').classList.add('hidden');
            showToast('success', '✓ Registrado', res.data.message);
            // El listener de Firestore actualizara el dashboard automaticamente
        } else {
            throw new Error(res.data.message || 'Error desconocido');
        }
    } catch(e) {
        errEl.textContent = `Error: ${e.message}`;
        errEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = '⚡ Registrar Evaluacion en Dashboard';
    }
}

// ─── Recuperación de Datos Perdidos ───
// Llama a force_sync_athlete por cada atleta para sincronizar
// mediciones que no llegaron al dashboard (ej: fallo del worker Ex-Gaussiano)
async function recoverMissingData() {
    const dateInput = prompt(
        'Ingresa la fecha a recuperar (formato YYYY-MM-DD):',
        new Date(Date.now() - 86400000).toLocaleDateString('en-CA') // ayer por defecto
    );
    if (!dateInput || !/^\d{4}-\d{2}-\d{2}$/.test(dateInput)) {
        return alert('Formato de fecha inválido. Usa YYYY-MM-DD (ej: 2026-06-17)');
    }

    if (!gAthletesCache.length) return alert('No hay atletas cargados. Espera un momento y vuelve a intentar.');

    const btn = document.getElementById('btn-recover');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Recuperando...'; }

    const forceFn = firebase.functions().httpsCallable('force_sync_athlete');
    let ok = 0, fail = 0;

    for (const athlete of gAthletesCache) {
        try {
            const res = await forceFn({ athleteId: athlete.id, date: dateInput });
            if (res.data.status === 'success') ok++;
            else fail++;
        } catch (e) {
            console.warn(`[RECOVER] Fallo para ${athlete.fullName}:`, e.message);
            fail++;
        }
    }

    if (btn) { btn.disabled = false; btn.textContent = '🔄 Recuperar Datos'; }
    alert(`Recuperación completada.\n✅ Sincronizados: ${ok}\n⚠️ Sin datos para esa fecha: ${fail}`);
}

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
    const newUserModal = document.getElementById('new-user-modal');
    const usersPanelModal = document.getElementById('users-panel-modal');
    const saasTenantModal = document.getElementById('saas-tenant-modal');
    const registrationModal = document.getElementById('registration-modal');
    
    if (e.target === athleteModal) {
        athleteModal.classList.add('hidden');
    }
    if (e.target === profileModal) {
        profileModal.classList.add('hidden');
    }
    if (e.target === sncModal) {
        sncModal.classList.add('hidden');
    }
    if (e.target === newUserModal) {
        newUserModal.classList.add('hidden');
    }
    if (e.target === usersPanelModal) {
        usersPanelModal.classList.add('hidden');
    }
    if (e.target === saasTenantModal) {
        saasTenantModal.classList.add('hidden');
    }
    if (e.target === registrationModal) {
        registrationModal.classList.add('hidden');
    }
});

// ==============================================================================
// USER MANAGEMENT (RBAC PANEL)
// ==============================================================================


async function loadDashboardUsers() {
    const tbody = document.getElementById('users-list-body');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:20px"><span class="kpi-spinner"></span> Cargando usuarios...</td></tr>';
    
    try {
        const fn = firebase.functions().httpsCallable('list_dashboard_users');
        const res = await fn();
        
        if (res.data.status === 'success') {
            const users = res.data.users || [];
            tbody.innerHTML = '';
            
            if (users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px">No hay usuarios</td></tr>';
                return;
            }
            
            users.forEach(u => {
                const date = new Date(u.creationTime).toLocaleDateString('es-CL');
                let roleBadge = '';
                if (u.role === 'ADMIN') roleBadge = '<span class="badge blue-badge">ADMIN</span>';
                else if (u.role === 'DEMO') roleBadge = '<span class="badge purple-badge">DEMO</span>';
                else roleBadge = '<span class="badge green-badge">COACH</span>';
                
                const teamBadge = u.team ? `<span class="badge badge-gray">${u.team}</span>` : `<span class="badge" style="background:rgba(255,255,255,0.1); color:#A1A1AA">Todas</span>`;
                
                const isDemo = u.email === 'demo@imedpredictor.com';
                const isMainAdmin = u.email === 'ps.patriciorubilar@gmail.com';
                let deleteBtn = '';
                if (isDemo) {
                    deleteBtn = `<button class="btn-icon" style="opacity:0.3; cursor:not-allowed" title="Demo inborrable">🗑</button>`;
                } else if (isMainAdmin) {
                    deleteBtn = `<button class="btn-icon" style="opacity:0.3; cursor:not-allowed" title="Admin principal protegido">🗑</button>`;
                } else {
                    deleteBtn = `<button class="btn-icon" style="color:#FF4D4D" title="Revocar Acceso" onclick="deleteDashboardUser('${u.uid}', '${u.email}')">🗑</button>`;
                }
                
                const editTeamBtn = isDemo || u.role === 'ADMIN' ? 
                    '' : 
                    `<button class="btn-icon" style="color:#00E5FF; margin-right:8px" title="Asignar Plantilla" onclick="openAssignTeamModal('${u.uid}', '${u.team || ''}')">⚙️</button>`;

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight:500; color:#fff">${u.email}</td>
                    <td>${roleBadge}</td>
                    <td>${teamBadge}</td>
                    <td style="color:var(--text-dim)">${date}</td>
                    <td>${editTeamBtn}${deleteBtn}</td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            throw new Error(res.data.message);
        }
    } catch(e) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:20px; color:#FF4D4D">Error: ${e.message}</td></tr>`;
    }
}

function openNewUserModal() {
    document.getElementById('new-user-email').value = '';
    document.getElementById('new-user-pass').value = '';
    document.getElementById('new-user-error').style.display = 'none';
    document.getElementById('new-user-success').style.display = 'none';
    
    const teamSelect = document.getElementById('new-user-team');
    if (teamSelect) {
        teamSelect.innerHTML = '<option value="">Todas (Sin restricción)</option>';
        const teams = [...new Set(gAthletesCache.map(a => a.team).filter(Boolean))].sort();
        teams.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t;
            opt.textContent = t;
            teamSelect.appendChild(opt);
        });
    }
    
    document.getElementById('new-user-modal').classList.remove('hidden');
}

function closeNewUserModal() {
    document.getElementById('new-user-modal').classList.add('hidden');
}

async function submitNewUser() {
    const email = document.getElementById('new-user-email').value.trim();
    const pass = document.getElementById('new-user-pass').value;
    const role = document.getElementById('new-user-role').value;
    const teamSelect = document.getElementById('new-user-team');
    const team = teamSelect ? teamSelect.value : '';
    const btn = document.getElementById('btn-new-user');
    const errEl = document.getElementById('new-user-error');
    const sucEl = document.getElementById('new-user-success');
    
    errEl.style.display = 'none';
    sucEl.style.display = 'none';
    
    if (!email || pass.length < 6) {
        errEl.textContent = 'El email es obligatorio y la contraseña debe tener min 6 caracteres.';
        errEl.style.display = 'block';
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="kpi-spinner"></span> Creando...';
    
    try {
        const fn = firebase.functions().httpsCallable('create_dashboard_user');
        const res = await fn({ email, password: pass, role, team });
        
        if (res.data.status === 'success') {
            sucEl.textContent = '✅ Usuario creado exitosamente.';
            sucEl.style.display = 'block';
            setTimeout(() => {
                closeNewUserModal();
                loadDashboardUsers();
            }, 1500);
        } else {
            throw new Error(res.data.message);
        }
    } catch (e) {
        errEl.textContent = `Error: ${e.message}`;
        errEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Crear Usuario';
    }
}

async function deleteDashboardUser(uid, email) {
    if (!confirm(`¿Estás seguro de que deseas REVOCAR EL ACCESO a ${email}?`)) return;
    
    try {
        const fn = firebase.functions().httpsCallable('delete_dashboard_user');
        const res = await fn({ uid });
        
        if (res.data.status === 'success') {
            showToast('success', 'Usuario Eliminado', `El acceso de ${email} ha sido revocado.`);
            loadDashboardUsers();
        } else {
            throw new Error(res.data.message);
        }
    } catch (e) {
        alert(`Error al eliminar: ${e.message}`);
    }
}

function openAssignTeamModal(uid, currentTeam) {
    document.getElementById('assign-team-error').style.display = 'none';
    document.getElementById('assign-team-success').style.display = 'none';
    document.getElementById('assign-team-uid').value = uid;
    
    const teamSelect = document.getElementById('assign-team-select');
    if (teamSelect) {
        teamSelect.innerHTML = '<option value="">Todas (Sin restricción)</option>';
        const teams = [...new Set(gAthletesCache.map(a => a.team).filter(Boolean))].sort();
        teams.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t;
            opt.textContent = t;
            if (t === currentTeam) opt.selected = true;
            teamSelect.appendChild(opt);
        });
    }
    
    document.getElementById('assign-team-modal').classList.remove('hidden');
}

function closeAssignTeamModal() {
    document.getElementById('assign-team-modal').classList.add('hidden');
}

async function submitAssignTeam() {
    const uid = document.getElementById('assign-team-uid').value;
    const teamSelect = document.getElementById('assign-team-select');
    const newTeam = teamSelect ? teamSelect.value : '';
    const btn = document.getElementById('btn-assign-team');
    const errEl = document.getElementById('assign-team-error');
    const sucEl = document.getElementById('assign-team-success');
    
    errEl.style.display = 'none';
    sucEl.style.display = 'none';
    btn.disabled = true;
    btn.innerHTML = '<span class="kpi-spinner"></span> Guardando...';
    
    try {
        const fn = firebase.functions().httpsCallable('update_dashboard_user_team');
        const res = await fn({ uid, team: newTeam.trim() });
        if (res.data.status === 'success') {
            sucEl.textContent = '✅ Plantilla actualizada exitosamente.';
            sucEl.style.display = 'block';
            setTimeout(() => {
                closeAssignTeamModal();
                loadDashboardUsers();
            }, 1000);
        } else {
            throw new Error(res.data.message);
        }
    } catch (e) {
        console.error(e);
        errEl.textContent = `Error al actualizar: ${e.message}`;
        errEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Guardar Cambios';
    }
}

// ─── SaaS Multi-Tenant & Subscription Control [NUEVO] ───
let gSaasTenantsCache = [];

window.loadSaasTenants = async function() {
    const tbody = document.getElementById('saas-tenants-body');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px"><span class="login-btn-spinner"></span> Cargando base de datos de inquilinos...</td></tr>`;

    try {
        const snap = await db.collection('tenants').orderBy('created_at', 'desc').get();
        gSaasTenantsCache = snap.docs.map(doc => ({ id: doc.id, ...doc.data() }));

        // Si la coleccion está vacia, inyectar inquilinos de prueba (Seed Data) para la postulación
        if (gSaasTenantsCache.length === 0) {
            await seedMockTenants();
            return;
        }

        renderTenantsTable();
    } catch (e) {
        console.error("Error al cargar tenants:", e);
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--red); padding:20px">Error de permisos o conexión al cargar base SaaS. Asegúrate de ser SUPER_ADMIN.</td></tr>`;
    }
};

async function seedMockTenants() {
    const mockData = [
        {
            id: 'colocolo',
            name: 'Club de Deportes Colo-Colo',
            plan: 'PRO',
            expiration: '2026-12-31',
            status: 'ACTIVE',
            admin_email: 'preparador.fisico@colocolo.cl',
            associationCode: 'COLO26',
            created_at: new Date()
        },
        {
            id: 'uchile',
            name: 'Club Universidad de Chile',
            plan: 'BASIC',
            expiration: '2026-08-15',
            status: 'ACTIVE',
            admin_email: 'kinesiologia@udechile.cl',
            associationCode: 'UCHI26',
            created_at: new Date(Date.now() - 86400000)
        },
        {
            id: 'clinicamedica',
            name: 'Centro de Medicina Deportiva Meds',
            plan: 'ENTERPRISE',
            expiration: '2027-06-30',
            status: 'ACTIVE',
            admin_email: 'contacto@meds.cl',
            associationCode: 'MEDS26',
            created_at: new Date(Date.now() - 86400000 * 2)
        },
        {
            id: 'valencia_fc',
            name: 'Valencia Football Club Academias',
            plan: 'TRIAL',
            expiration: '2026-07-10',
            status: 'EXPIRED',
            admin_email: 'academias@valencia.es',
            associationCode: 'VALE26',
            created_at: new Date(Date.now() - 86400000 * 20)
        }
    ];

    for (const tenant of mockData) {
        await db.collection('tenants').doc(tenant.id).set(tenant);
    }
    await loadSaasTenants();
}

function renderTenantsTable() {
    const tbody = document.getElementById('saas-tenants-body');
    if (!tbody) return;

    if (gSaasTenantsCache.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px">No hay inquilinos registrados.</td></tr>`;
        return;
    }

    tbody.innerHTML = gSaasTenantsCache.map(t => {
        const badgeColor = t.status === 'ACTIVE' ? 'badge-green' : t.status === 'EXPIRED' ? 'badge-yellow' : 'badge-red';
        const actionBtn = t.status === 'ACTIVE' 
            ? `<button class="btn-mini" style="background:rgba(255,77,77,0.1); border:1px solid rgba(255,77,77,0.2); color:var(--red)" onclick="switchTenantStatus('${t.id}', 'SUSPENDED')">Suspender</button>`
            : `<button class="btn-mini" style="background:rgba(50,215,75,0.1); border:1px solid rgba(50,215,75,0.2); color:var(--green)" onclick="switchTenantStatus('${t.id}', 'ACTIVE')">Reactivar</button>`;

        return `
            <tr>
                <td style="font-weight:700" class="mono-cell">${t.id}</td>
                <td>
                    <div style="font-weight:600; color:#fff">${t.name}</div>
                    <div style="font-size:11px; color:#636375">${t.admin_email}</div>
                    <div style="font-size:11px; color:#00E5FF; font-weight:700; margin-top:2px">Código: <span class="mono-cell" style="background:rgba(0,229,255,0.1); padding:2px 6px; border-radius:4px">${t.associationCode || 'IMED-MOCKCODE'}</span></div>
                </td>
                <td><span class="badge blue-badge">${t.plan}</span></td>
                <td>${t.expiration || 'Sin límite (Enterprise)'}</td>
                <td><span class="badge ${badgeColor}">${t.status}</span></td>
                <td style="display:flex; gap:6px">${actionBtn}</td>
            </tr>
        `;
    }).join('');
}

window.switchTenantStatus = async function(tenantId, newStatus) {
    try {
        await db.collection('tenants').doc(tenantId).update({ status: newStatus });
        showToast('success', 'Inquilino Actualizado', `El estado del tenant ${tenantId} ha cambiado a ${newStatus}.`);
        await loadSaasTenants();
    } catch (e) {
        console.error(e);
        showToast('error', 'Error SaaS', 'No tienes permisos de SuperAdmin para modificar inquilinos.');
    }
};

window.openNewTenantModal = function() {
    document.getElementById('saas-tenant-modal').classList.remove('hidden');
};

window.closeTenantModal = function() {
    document.getElementById('saas-tenant-modal').classList.add('hidden');
};

window.saveNewTenant = async function(event) {
    event.preventDefault();
    const btn = event.submitter || event.target.querySelector('button[type="submit"]');
    const origText = btn.innerHTML;

    btn.disabled = true;
    btn.textContent = 'Aprovisionando base de datos...';

    const id = document.getElementById('tenant-id-input').value.toLowerCase().replace(/[^a-z0-9]/g, '');
    const name = document.getElementById('tenant-name-input').value.trim();
    const plan = document.getElementById('tenant-plan-input').value;
    const email = document.getElementById('tenant-email-input').value.trim();

    const today = new Date();
    let expiration = "";
    if (plan === 'TRIAL') {
        today.setDate(today.getDate() + 14);
        expiration = today.toISOString().split('T')[0];
    } else if (plan === 'BASIC' || plan === 'PRO') {
        today.setDate(today.getDate() + 30);
        expiration = today.toISOString().split('T')[0];
    }

    // Generar un código único legible de 6 caracteres alfanuméricos
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let codeStr = '';
    for (let i = 0; i < 6; i++) {
        codeStr += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    const associationCode = codeStr;

    const newTenant = {
        id,
        name,
        plan,
        expiration,
        status: 'ACTIVE',
        admin_email: email,
        associationCode,
        created_at: new Date()
    };

    try {
        await db.collection('tenants').doc(id).set(newTenant);
        showToast('success', 'Tenant Aprovisionado', `Base de datos aislada para ${name} lista.`);
        closeTenantModal();
        await loadSaasTenants();
    } catch (e) {
        console.error(e);
        showToast('error', 'Fallo Aprovisionamiento', 'Error de permisos al dar de alta el inquilino.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = origText;
    }
};

// ─── Simulación Pasarela Stripe & Cobros ───
window.simulateCheckout = function(planName) {
    showToast('info', 'Redirección Pasarela', `Conectando con Stripe Checkout para plan ${planName}...`);
    setTimeout(async () => {
        const confirmar = confirm(`[SIMULADOR STRIPE] ¿Deseas autorizar la suscripción de pago mensual para el plan ${planName}?`);
        if (confirmar) {
            try {
                // Actualizar plan en base de datos si tiene tenant
                if (window.currentUserTenantId) {
                    await db.collection('tenants').doc(window.currentUserTenantId).update({ plan: planName.toUpperCase() });
                    showToast('success', 'Plan Actualizado', `¡Gracias por tu compra! Tu plan ha sido actualizado a ${planName}.`);
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showToast('success', 'Suscripción Procesada', `¡Gracias por tu compra! Tu licencia ${planName} se encuentra activa.`);
                }
            } catch (e) {
                console.error(e);
                showToast('error', 'Error de Compra', 'No se pudo actualizar el plan.');
            }
        }
    }, 1000);
};

window.simulateBillingPortal = function() {
    showToast('info', 'Stripe Billing Portal', 'Conectando con el Portal de Facturación de Stripe...');
    setTimeout(() => {
        alert('[PORTAL DE FACTURACIÓN MOCK] Aquí el cliente puede actualizar su tarjeta, ver facturas previas y descargar comprobantes de pago.');
    }, 800);
};

window.cancelSubscription = function() {
    const confirmar = confirm("¿Estás seguro de que deseas eliminar tu plan actual y cancelar tu suscripción? Perderás acceso a los reportes avanzados.");
    if (confirmar) {
        setTimeout(async () => {
            try {
                if (window.currentUserTenantId) {
                    await db.collection('tenants').doc(window.currentUserTenantId).update({ status: 'SUSPENDED', plan: 'NINGUNO' });
                    showToast('success', 'Suscripción Eliminada', 'Tu plan ha sido cancelado con éxito.');
                    setTimeout(() => auth.signOut(), 2000);
                } else {
                    showToast('success', 'Plan Cancelado', 'Tu suscripción ha sido eliminada con éxito.');
                }
            } catch (e) {
                console.error(e);
                showToast('error', 'Error al Cancelar', 'No se pudo cancelar el plan.');
            }
        }, 500);
    }
};

