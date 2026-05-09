/* ═══════════════════════════════════════════
   IMED PREDICTOR — app.js
   Firebase + Motor IVN + UI Logic
════════════════════════════════════════════ */

// ─── Firebase Config (app-imed-sport) ───
const firebaseConfig = {
  apiKey:            "AIzaSyA-eVf8UncVMgN6mDgsgjqbj2hhPmRDjUs",
  authDomain:        "app-imed-sport.firebaseapp.com",
  projectId:         "app-imed-sport",
  storageBucket:     "app-imed-sport.firebasestorage.app",
  messagingSenderId: "300860465249",
  appId:             "1:300860465249:web:08f49c42e30a7bab42ca20"
};
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();

// ─── Thresholds (configurable) ───
let THRESH = { iriCritical: 60, lapses: 2, iriOptimal: 85 };

// ─── State ───
let allPerformance = [];
let correlationChart = null;
let selectedFile = null;
let unsubscribe = null;

// ═══════════════════════════════════════════
// IVN ENGINE
// ═══════════════════════════════════════════
function calcIVN(iri, lapses, externalLoad, meanLoad) {
  if (iri < THRESH.iriCritical && externalLoad > meanLoad)
    return { level: 'RED',    label: 'RIESGO CRÍTICO',       action: 'Optimizar',    badgeClass: 'badge-red',    ringClass: 'ring-red',    btnClass: 'red' };
  if (lapses > THRESH.lapses)
    return { level: 'YELLOW', label: 'RIESGO COORDINACIÓN',  action: 'Reprogramar',  badgeClass: 'badge-yellow', ringClass: 'ring-yellow', btnClass: 'yellow' };
  if (iri > THRESH.iriOptimal && externalLoad >= meanLoad)
    return { level: 'GREEN',  label: 'ADAPTACIÓN ÓPTIMA',    action: 'Mantener',     badgeClass: 'badge-green',  ringClass: 'ring-green',  btnClass: 'green' };
  return   { level: 'GREEN',  label: 'ESTABLE',               action: 'Mantener',     badgeClass: 'badge-green',  ringClass: 'ring-green',  btnClass: 'green' };
}

// ═══════════════════════════════════════════
// FIRESTORE REAL-TIME LISTENER
// ═══════════════════════════════════════════
function startRealtimeListener() {
  const today = new Date();
  today.setHours(0,0,0,0);
  if (unsubscribe) unsubscribe();

  unsubscribe = db.collection('Daily_Performance')
    .orderBy('timestamp', 'desc')
    .limit(100)
    .onSnapshot(snap => {
      allPerformance = snap.docs.map(d => ({ id: d.id, ...d.data() }));
      renderDashboard();
      renderAthletesTable();
      populateAthleteSelects();
    }, err => {
      console.warn('Firestore listener error:', err);
      loadDemoData();
    });
}

// ─── Demo data when Firestore is unavailable ───
function loadDemoData() {
  allPerformance = [
    { id:'ATH001_2026-05-09', athleteId:'ATH001', athleteName:'Sergio Ramos',     position:'Defensa', iri:54, lapses:3, gps:{ decel_high:22, accel_high:18, max_speed:31.2, sprint_distance:580 }, risk_level:'RED',    timestamp:{seconds:Date.now()/1000} },
    { id:'ATH002_2026-05-09', athleteId:'ATH002', athleteName:'Kevin De Bruyne',  position:'Mediocampo', iri:72, lapses:4, gps:{ decel_high:14, accel_high:12, max_speed:28.5, sprint_distance:420 }, risk_level:'YELLOW', timestamp:{seconds:Date.now()/1000} },
    { id:'ATH003_2026-05-09', athleteId:'ATH003', athleteName:'Marco Reus',       position:'Delantero', iri:91, lapses:1, gps:{ decel_high:18, accel_high:16, max_speed:33.1, sprint_distance:690 }, risk_level:'GREEN',  timestamp:{seconds:Date.now()/1000} },
    { id:'ATH004_2026-05-09', athleteId:'ATH004', athleteName:'Virgil van Dijk',  position:'Defensa', iri:58, lapses:1, gps:{ decel_high:20, accel_high:14, max_speed:29.0, sprint_distance:510 }, risk_level:'RED',    timestamp:{seconds:Date.now()/1000} },
    { id:'ATH005_2026-05-09', athleteId:'ATH005', athleteName:'Luka Modrić',      position:'Mediocampo', iri:88, lapses:0, gps:{ decel_high:11, accel_high:10, max_speed:27.3, sprint_distance:380 }, risk_level:'GREEN',  timestamp:{seconds:Date.now()/1000} },
  ];
  renderDashboard();
  renderAthletesTable();
  populateAthleteSelects();
}

// ═══════════════════════════════════════════
// RENDER DASHBOARD
// ═══════════════════════════════════════════
function renderDashboard() {
  const meanLoad = allPerformance.reduce((s,p) => s + (p.gps?.decel_high||0), 0) / (allPerformance.length||1);
  let counts = { RED:0, YELLOW:0, GREEN:0 };

  const items = allPerformance.map(p => {
    const ivn = calcIVN(p.iri||0, p.lapses||0, p.gps?.decel_high||0, meanLoad);
    counts[ivn.level]++;
    const initials = (p.athleteName||'?').split(' ').map(w=>w[0]).join('').slice(0,2);
    return `
      <div class="athlete-card" onclick="openModal('${p.id}')">
        <div class="athlete-avatar">
          ${initials}
          <div class="risk-ring ${ivn.ringClass}"></div>
        </div>
        <div class="athlete-info">
          <div class="athlete-name">${p.athleteName || p.athleteId}</div>
          <div class="athlete-pos">${p.position || '—'}</div>
        </div>
        <div class="athlete-metrics">
          <div class="metric-mini">
            <div class="val ${p.iri < THRESH.iriCritical ? 'text-red' : p.iri > THRESH.iriOptimal ? 'text-green' : 'text-yellow'}">${Math.round(p.iri||0)}</div>
            <div class="lbl">IRI</div>
          </div>
          <div class="metric-mini">
            <div class="val ${(p.lapses||0) > THRESH.lapses ? 'text-red' : 'text-green'}">${p.lapses||0}</div>
            <div class="lbl">LAPSES</div>
          </div>
          <div class="metric-mini">
            <div class="val">${p.gps?.decel_high||0}</div>
            <div class="lbl">DESACEL.</div>
          </div>
        </div>
        <span class="risk-badge ${ivn.badgeClass}">${ivn.label}</span>
        <button class="action-btn ${ivn.btnClass}">${ivn.action}</button>
      </div>`;
  });

  document.getElementById('athlete-list').innerHTML = items.length
    ? items.join('') : '<div class="empty-state"><div class="empty-icon">✓</div><p>Sin datos de hoy</p></div>';

  // KPIs
  document.getElementById('kpi-critical').textContent    = counts.RED;
  document.getElementById('kpi-coordination').textContent = counts.YELLOW;
  document.getElementById('kpi-optimal').textContent     = counts.GREEN;
  document.getElementById('kpi-total').textContent       = allPerformance.length;
  document.getElementById('count-critical').textContent  = counts.RED;
  document.getElementById('count-warning').textContent   = counts.YELLOW;
  document.getElementById('count-optimal').textContent   = counts.GREEN;

  updateChart();
}

// ═══════════════════════════════════════════
// CORRELATION CHART (IRI vs Desaceleraciones)
// ═══════════════════════════════════════════
function updateChart() {
  const meanLoad = allPerformance.reduce((s,p) => s+(p.gps?.decel_high||0),0) / (allPerformance.length||1);
  const datasets = { RED:[], YELLOW:[], GREEN:[] };

  allPerformance.forEach(p => {
    const ivn = calcIVN(p.iri||0, p.lapses||0, p.gps?.decel_high||0, meanLoad);
    datasets[ivn.level].push({ x: p.gps?.decel_high||0, y: p.iri||0, label: p.athleteName||p.athleteId });
  });

  const cfg = {
    type: 'scatter',
    data: {
      datasets: [
        { label:'Riesgo Crítico',       data: datasets.RED,    backgroundColor:'rgba(255,77,77,0.8)',   pointRadius:8, pointHoverRadius:11 },
        { label:'Riesgo Coordinación',  data: datasets.YELLOW, backgroundColor:'rgba(255,214,10,0.8)',  pointRadius:8, pointHoverRadius:11 },
        { label:'Adaptación Óptima',    data: datasets.GREEN,  backgroundColor:'rgba(50,215,75,0.8)',   pointRadius:8, pointHoverRadius:11 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => `${ctx.raw.label || ''} — IRI:${ctx.raw.y} / Desacel:${ctx.raw.x}` } }
      },
      scales: {
        x: { title:{ display:true, text:'Desaceleraciones Altas', color:'#636375' }, grid:{ color:'rgba(255,255,255,0.05)' }, ticks:{ color:'#636375' } },
        y: { title:{ display:true, text:'IRI (0-100)', color:'#636375' }, grid:{ color:'rgba(255,255,255,0.05)' }, ticks:{ color:'#636375' }, min:0, max:100 }
      }
    }
  };

  const canvas = document.getElementById('correlationChart');
  if (correlationChart) correlationChart.destroy();
  correlationChart = new Chart(canvas, cfg);
}

// ═══════════════════════════════════════════
// ATHLETES TABLE
// ═══════════════════════════════════════════
function renderAthletesTable(filter='') {
  const meanLoad = allPerformance.reduce((s,p)=>s+(p.gps?.decel_high||0),0)/(allPerformance.length||1);
  const rows = allPerformance
    .filter(p => !filter || (p.athleteName||'').toLowerCase().includes(filter.toLowerCase()))
    .map(p => {
      const ivn = calcIVN(p.iri||0, p.lapses||0, p.gps?.decel_high||0, meanLoad);
      const d = new Date((p.timestamp?.seconds||0)*1000).toLocaleDateString('es-CL');
      return `<tr onclick="openModal('${p.id}')">
        <td><strong>${p.athleteName||p.athleteId}</strong></td>
        <td>${p.position||'—'}</td>
        <td class="${p.iri<THRESH.iriCritical?'text-red':p.iri>THRESH.iriOptimal?'text-green':'text-yellow'}">${Math.round(p.iri||0)}</td>
        <td class="${(p.lapses||0)>THRESH.lapses?'text-red':'text-green'}">${p.lapses||0}</td>
        <td>${p.gps?.decel_high||0}</td>
        <td>${p.gps?.max_speed||0} km/h</td>
        <td><span class="risk-badge ${ivn.badgeClass}">${ivn.label}</span></td>
        <td>${d}</td>
      </tr>`;
    });

  document.getElementById('athletes-table-container').innerHTML = rows.length
    ? `<table class="athletes-table"><thead><tr>
        <th>ATLETA</th><th>POSICIÓN</th><th>IRI</th><th>LAPSES</th>
        <th>DESACEL.</th><th>VEL. MÁX</th><th>ESTADO IVN</th><th>FECHA</th>
      </tr></thead><tbody>${rows.join('')}</tbody></table>`
    : '<div class="empty-state"><div class="empty-icon">🔍</div><p>No se encontraron atletas</p></div>';
}

function filterAthletes(v) { renderAthletesTable(v); }

// ═══════════════════════════════════════════
// ATHLETE MODAL
// ═══════════════════════════════════════════
function openModal(id) {
  const p = allPerformance.find(x => x.id === id);
  if (!p) return;
  const meanLoad = allPerformance.reduce((s,x)=>s+(x.gps?.decel_high||0),0)/(allPerformance.length||1);
  const ivn = calcIVN(p.iri||0, p.lapses||0, p.gps?.decel_high||0, meanLoad);

  document.getElementById('modal-content').innerHTML = `
    <div class="modal-header">
      <div>
        <div class="panel-label">PERFIL DE NEURO-EVALUACIÓN</div>
        <h2 class="panel-title">${p.athleteName||p.athleteId}</h2>
      </div>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div style="margin-bottom:16px">
      <span class="risk-badge ${ivn.badgeClass}" style="font-size:12px;padding:6px 14px">${ivn.label}</span>
    </div>
    <div class="modal-metric-row">
      <div class="modal-metric">
        <div class="val ${p.iri<THRESH.iriCritical?'text-red':p.iri>THRESH.iriOptimal?'text-green':'text-yellow'}">${Math.round(p.iri||0)}</div>
        <div class="lbl">IRI</div>
      </div>
      <div class="modal-metric">
        <div class="val ${(p.lapses||0)>THRESH.lapses?'text-red':'text-green'}">${p.lapses||0}</div>
        <div class="lbl">LAPSES PVT</div>
      </div>
      <div class="modal-metric">
        <div class="val">${p.gps?.decel_high||0}</div>
        <div class="lbl">DESACEL. ALTAS</div>
      </div>
      <div class="modal-metric">
        <div class="val">${p.gps?.accel_high||0}</div>
        <div class="lbl">ACEL. ALTAS</div>
      </div>
      <div class="modal-metric">
        <div class="val">${p.gps?.max_speed||0}</div>
        <div class="lbl">VEL. MÁX (km/h)</div>
      </div>
      <div class="modal-metric">
        <div class="val">${p.gps?.sprint_distance||0}</div>
        <div class="lbl">DIST. SPRINT (m)</div>
      </div>
    </div>
    <div style="padding:16px;background:var(--glass);border-radius:10px;border:1px solid var(--border)">
      <div class="history-title">RECOMENDACIÓN DEL MOTOR $IVN$</div>
      <p style="font-size:13px;color:var(--text-2);line-height:1.7">
        ${ivn.level==='RED'
          ? `<strong class="text-red">⚠ Acción Inmediata:</strong> El atleta presenta IRI de ${Math.round(p.iri||0)} (umbral crítico: ${THRESH.iriCritical}) combinado con carga mecánica elevada. Riesgo inminente de falla neuromuscular. Recomendación: <strong>Optimizar</strong> la sesión — reducir volumen de desaceleraciones en un 40-60%.`
          : ivn.level==='YELLOW'
          ? `<strong class="text-yellow">🔄 Reprogramar:</strong> Se detectaron ${p.lapses||0} lapsos de atención (umbral: ${THRESH.lapses}). El SNC ha perdido el timing neuro-motor. Riesgo articular elevado. Recomendación: <strong>Reprogramar</strong> la carga — priorizar recuperación activa.`
          : `<strong class="text-green">✓ Estado Óptimo:</strong> IRI de ${Math.round(p.iri||0)} indica alta disponibilidad neurológica. Ventana de supercompensación activa. Mantener planificación actual de carga.`}
      </p>
    </div>`;

  document.getElementById('athlete-modal').classList.remove('hidden');
}

function closeModal(e) {
  if (!e || e.target.id === 'athlete-modal') {
    document.getElementById('athlete-modal').classList.add('hidden');
  }
}

// ═══════════════════════════════════════════
// CSV UPLOAD & IVN CALCULATION (client-side)
// ═══════════════════════════════════════════
const GPS_COLUMN_MAP = {
  accel_high:      ['accel_high','High Accels','Aceleraciones Altas','HighAccel','high_accel'],
  decel_high:      ['decel_high','High Decels','Desaceleraciones Altas','HighDecel','high_decel'],
  max_speed:       ['max_speed','Max Speed','Velocidad Máxima','MaxSpeed','vel_max'],
  sprint_distance: ['sprint_distance','Sprint Distance','Distancia Sprint','SprintDist','dist_sprint']
};

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) throw new Error('CSV vacío o inválido');
  const headers = lines[0].split(',').map(h=>h.trim());
  const rows = [];
  for (let i=1; i<lines.length; i++) {
    const vals = lines[i].split(',');
    const row = {};
    headers.forEach((h,j) => row[h] = (vals[j]||'').trim());
    rows.push(row);
  }
  return { headers, rows };
}

function mapGPSColumns(headers, row) {
  const out = {};
  for (const [std, aliases] of Object.entries(GPS_COLUMN_MAP)) {
    const col = aliases.find(a => headers.includes(a));
    out[std] = col ? parseFloat(row[col])||0 : 0;
  }
  return out;
}

function handleDragOver(e) { e.preventDefault(); document.getElementById('dropzone').classList.add('drag-over'); }
function handleDragLeave()  { document.getElementById('dropzone').classList.remove('drag-over'); }
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
}
function handleFileSelect(e) { if(e.target.files[0]) setFile(e.target.files[0]); }
function setFile(file) {
  selectedFile = file;
  document.getElementById('dropzone-filename').textContent = `✓ ${file.name}`;
  document.getElementById('btn-process').disabled = !document.getElementById('upload-athlete').value;
}

async function processCSV() {
  if (!selectedFile) return;
  
  const athleteId = document.getElementById('upload-athlete').value;
  const date      = document.getElementById('upload-date').value || new Date().toISOString().slice(0,10);
  
  if (!athleteId) {
    showToast('error', 'Error', 'Selecciona un atleta primero');
    return;
  }

  showUploadResult('info', 'Subiendo archivo y procesando con Motor IVN...');
  document.getElementById('btn-process').disabled = true;

  try {
    // 1. Subir a Firebase Storage
    const storageRef = firebase.storage().ref();
    const filePath = `gps/${athleteId}/${date}/${selectedFile.name}`;
    const fileRef = storageRef.child(filePath);
    
    await fileRef.put(selectedFile);
    console.log('Archivo subido a:', filePath);

    // 2. Llamar a la Cloud Function para procesar
    const processFn = firebase.functions().httpsCallable('process_gps_csv');
    const result = await processFn({ filePath: filePath });
    
    const data = result.data;
    if (data.status === 'success') {
      showUploadResult('success', `
        <strong>Análisis Completado:</strong><br>
        Nivel de Riesgo: <span class="badge-${data.riskLevel.toLowerCase()}">${data.ivnLabel}</span><br>
        Documento guardado en <code>Daily_Performance</code>.
      `);
      showToast('success', '✓ Motor IVN', `Análisis finalizado: ${data.ivnLabel}`);
    } else {
      throw new Error(data.message || 'Error desconocido en el motor');
    }

  } catch (err) {
    console.error(err);
    showUploadResult('error', `Error: ${err.message}`);
    showToast('error', '✕ Fallo', 'No se pudo completar el análisis neuro-mecánico');
  } finally {
    document.getElementById('btn-process').disabled = false;
  }
}

function showUploadResult(type, html) {
  const el = document.getElementById('upload-result');
  el.className = `upload-result ${type}`;
  el.innerHTML = `<strong>${type==='success'?'✓ Éxito':'✕ Error'}:</strong> ${html}`;
  el.classList.remove('hidden');
}

// ═══════════════════════════════════════════
// NEURO-REPORTS
// ═══════════════════════════════════════════
function populateAthleteSelects() {
  const unique = [...new Map(allPerformance.map(p=>[p.athleteId,p])).values()];
  ['report-athlete-select','upload-athlete'].forEach(id => {
    const sel = document.getElementById(id);
    const cur = sel.value;
    sel.innerHTML = `<option value="">Seleccionar atleta…</option>`;
    unique.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.athleteId; opt.textContent = p.athleteName || p.athleteId;
      sel.appendChild(opt);
    });
    if (cur) sel.value = cur;
  });
}

function loadAthleteReport(athleteId) {
  if (!athleteId) { document.getElementById('report-container').innerHTML='<div class="empty-state"><div class="empty-icon">📊</div><p>Selecciona un atleta</p></div>'; return; }
  const records = allPerformance.filter(p=>p.athleteId===athleteId).slice(0,14);
  if (!records.length) { document.getElementById('report-container').innerHTML='<div class="empty-state"><div class="empty-icon">📭</div><p>Sin registros</p></div>'; return; }

  const labels = records.map(p=>p.date||'').reverse();
  const iriVals = records.map(p=>p.iri||0).reverse();
  const decelVals = records.map(p=>p.gps?.decel_high||0).reverse();

  document.getElementById('report-container').innerHTML = `
    <div class="report-chart-container"><canvas id="reportChart"></canvas></div>
    <div class="chart-legend">
      <div class="legend-item"><span class="legend-dot" style="background:#32D74B"></span> IRI</div>
      <div class="legend-item"><span class="legend-dot" style="background:#FF4D4D"></span> Desaceleraciones</div>
    </div>`;

  new Chart(document.getElementById('reportChart'), {
    type:'line',
    data:{ labels, datasets:[
      { label:'IRI', data:iriVals, borderColor:'#32D74B', backgroundColor:'rgba(50,215,75,0.08)', tension:0.4, borderWidth:2, pointRadius:4, yAxisID:'y' },
      { label:'Desacel.', data:decelVals, borderColor:'#FF4D4D', backgroundColor:'rgba(255,77,77,0.08)', tension:0.4, borderWidth:2, pointRadius:4, yAxisID:'y1' }
    ]},
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ display:false } },
      scales:{
        y:  { position:'left',  min:0, max:100, grid:{ color:'rgba(255,255,255,0.05)' }, ticks:{ color:'#636375' } },
        y1: { position:'right', grid:{ drawOnChartArea:false }, ticks:{ color:'#636375' } }
      }
    }
  });
}

// ═══════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════
const VIEWS = ['dashboard','athletes','reports','upload','settings'];
const TITLES = { dashboard:'Centro de Mando de Rendimiento', athletes:'Gestión de Plantilla', reports:'Historial de Neuro-evaluaciones', upload:'Adaptador Universal GPS', settings:'Configuración del Sistema' };

function showView(name) {
  VIEWS.forEach(v => {
    document.getElementById(`view-${v}`).classList.toggle('active', v===name);
    document.getElementById(`nav-${v}`)?.classList.toggle('active', v===name);
  });
  document.getElementById('page-title').textContent = TITLES[name]||name;
}

// ═══════════════════════════════════════════
// SETTINGS
// ═══════════════════════════════════════════
function saveSettings() {
  THRESH.iriCritical = parseInt(document.getElementById('threshold-iri').value)||60;
  THRESH.lapses      = parseInt(document.getElementById('threshold-lapses').value)||2;
  THRESH.iriOptimal  = parseInt(document.getElementById('threshold-iri-opt').value)||85;
  renderDashboard(); renderAthletesTable();
  showToast('success','✓ Guardado','Umbrales del algoritmo $IVN$ actualizados');
}

// ═══════════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════════
function showToast(type, title, sub) {
  const icons = { success:'✓', error:'✕', info:'ℹ' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<div class="toast-icon">${icons[type]||'ℹ'}</div><div class="toast-text"><div class="toast-title">${title}</div><div class="toast-sub">${sub}</div></div>`;
  document.body.appendChild(t);
  setTimeout(()=>t.remove(), 4000);
}

// ═══════════════════════════════════════════
// REFRESH
// ═══════════════════════════════════════════
function refreshData() { showToast('info','↻ Actualizando','Sincronizando con Firebase…'); }

// ═══════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('live-date').textContent = new Date().toLocaleDateString('es-CL',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
  document.getElementById('upload-date').value = new Date().toISOString().slice(0,10);
  startRealtimeListener();
});
