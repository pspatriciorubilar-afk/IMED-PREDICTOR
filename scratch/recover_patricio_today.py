"""
Busqueda profunda de datos de Patricio Rubilar para hoy.
Revisa measurements con y sin campo date, y fuerza la sincronizacion.
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

SA_PATH = os.path.join(os.path.dirname(__file__), '..', 'functions', 'serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(SA_PATH))

db = firestore.client()

ATHLETE_ID = 'patricio_rubilar_45'
today      = datetime.now().strftime('%Y-%m-%d')  # 2026-06-18

print(f"\n{'='*60}")
print(f"  Busqueda profunda: Patricio Rubilar")
print(f"  Fecha local hoy: {today}")
print(f"{'='*60}\n")

# ── 1. Buscar TODOS los measurements (sin filtro de fecha) ────────────────────
print(">> Todos los measurements de Patricio (ultimos 10):\n")
all_meas = list(
    db.collection('athletes').document(ATHLETE_ID)
      .collection('measurements')
      .order_by('timestamp', direction=firestore.Query.DESCENDING)
      .limit(10)
      .stream()
)

if not all_meas:
    print("   [!] No se encontraron measurements de ningun tipo.\n")
else:
    for doc in all_meas:
        m = doc.to_dict()
        ts  = m.get('timestamp', '?')
        dt  = m.get('date', '[sin campo date]')
        iri = m.get('iri', '?')
        pvt = m.get('pvt', {})
        lapses = pvt.get('metrics', {}).get('lapses', '?')
        n_trials = pvt.get('metrics', {}).get('n_trials', len(pvt.get('metrics', {}).get('trials', [])))
        sync = m.get('sync_method', '?')
        print(f"   Doc ID : {doc.id}")
        print(f"   date   : {dt}")
        print(f"   ts     : {ts}")
        print(f"   IRI    : {iri}")
        print(f"   lapses : {lapses}")
        print(f"   trials : {n_trials}")
        print(f"   sync   : {sync}")
        print()

# ── 2. Buscar en Daily_Performance para hoy ───────────────────────────────────
print(f">> Daily_Performance para {today}:\n")
dp_docs = list(
    db.collection('Daily_Performance')
      .where('athleteId', '==', ATHLETE_ID)
      .where('date', '==', today)
      .stream()
)
if dp_docs:
    for doc in dp_docs:
        d = doc.to_dict()
        print(f"   [OK] Doc: {doc.id} | IRI: {d.get('iri','?')} | sync: {d.get('sync_method','?')}")
else:
    print(f"   [MISS] No hay entrada en Daily_Performance para hoy.")

# ── 3. Si hay measurement de hoy pero no en Daily_Performance → forzar sync ──
print(f"\n{'─'*60}")
print(">> Buscando measurement de hoy para forzar sync si falta...\n")

found_today = None
for doc in all_meas:
    m = doc.to_dict()
    dt = m.get('date', '')

    # Intentar tambien extraer fecha del timestamp string
    ts_str = str(m.get('timestamp', ''))
    ts_date = ts_str[:10] if len(ts_str) >= 10 else ''

    if dt == today or ts_date == today:
        found_today = m
        print(f"   [ENCONTRADO] measurement de hoy: date='{dt}', ts='{ts_str[:19]}'")
        break

if found_today and not dp_docs:
    print("   >> Sincronizando a Daily_Performance ahora...\n")

    # Obtener nombre del atleta
    athlete_doc = db.collection('athletes').document(ATHLETE_ID).get()
    ad = athlete_doc.to_dict() if athlete_doc.exists else {}
    athlete_name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip() or ATHLETE_ID

    pvt      = found_today.get('pvt', {})
    metrics  = pvt.get('metrics', {})
    mean_lat = metrics.get('meanLatency', found_today.get('latency', 0))

    payload = {
        'athleteId':   ATHLETE_ID,
        'athleteName': athlete_name,
        'date':        today,
        'iri':         found_today.get('iri', 0),
        'status':      found_today.get('status', ''),
        'lapses':      metrics.get('lapses', 0),
        'latency':     mean_lat,
        'wellness':    found_today.get('wellness'),
        'pvt':         pvt,
        'timestamp':   firestore.SERVER_TIMESTAMP,
        'sync_method': 'script_deep_recovery',
    }

    doc_id = f"{ATHLETE_ID}_{today}"
    db.collection('Daily_Performance').document(doc_id).set(payload, merge=True)
    print(f"   [SYNC OK] Patricio Rubilar sincronizado para {today}")
    print(f"   IRI: {found_today.get('iri','?')} | lapses: {metrics.get('lapses','?')}")
    print(f"\n   >> El dashboard deberia mostrar el dato en segundos.")

elif found_today and dp_docs:
    print("   [YA ESTABA] El dato ya existe en Daily_Performance. El dashboard deberia mostrarlo.")

else:
    print("   [SIN DATOS] No se encontro ninguna medicion de hoy en measurements.")
    print("   Posibles causas:")
    print("   1. La app no guardo en Firestore (verificar conexion del dispositivo)")
    print("   2. El measurement se guardo con una fecha diferente (zona horaria)")
    print("   3. La prueba se guardo solo localmente en Isar/Hive (pendiente de sync)")

print()
