"""
IMED PREDICTOR - Script de Diagnostico y Recuperacion
Verifica datos de ayer y hoy en Firestore y los sincroniza a Daily_Performance.
"""
import sys
import os
import io

# Forzar UTF-8 en stdout para Windows (evita UnicodeEncodeError con emojis)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

# -- Init ----------------------------------------------------------------------
SA_PATH = os.path.join(os.path.dirname(__file__), '..', 'functions', 'serviceAccount.json')
if not firebase_admin._apps:
    cred = credentials.Certificate(SA_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -- Fechas a revisar ----------------------------------------------------------
now_local = datetime.now()
today     = now_local.strftime('%Y-%m-%d')
yesterday = (now_local - timedelta(days=1)).strftime('%Y-%m-%d')
dates     = [yesterday, today]

print(f"\n{'='*60}")
print(f"  IMED PREDICTOR - Diagnostico de Datos")
print(f"  Revisando fechas: {yesterday} y {today}")
print(f"{'='*60}\n")

# -- 1. Listar atletas ---------------------------------------------------------
athletes_docs = list(db.collection('athletes').stream())
athletes = []
for doc in athletes_docs:
    d = doc.to_dict()
    name = f"{d.get('firstName','')} {d.get('lastName','')}".strip() or doc.id
    athletes.append({'id': doc.id, 'name': name})

print(f"[INFO] Atletas en sistema: {len(athletes)}")
for a in athletes:
    print(f"   - {a['name']} (ID: {a['id']})")

# -- 2. Verificar Daily_Performance --------------------------------------------
print(f"\n{'-'*60}")
print("DAILY_PERFORMANCE - Estado actual:")

dp_existing = set()
for date in dates:
    docs = list(db.collection('Daily_Performance').where('date', '==', date).stream())
    if docs:
        for doc in docs:
            d = doc.to_dict()
            dp_existing.add(f"{d.get('athleteId','')}_{date}")
            print(f"   [OK] [{date}] {d.get('athleteName', d.get('athleteId','?'))} | IRI: {d.get('iri','?')} | sync: {d.get('sync_method','?')}")
    else:
        print(f"   [MISS] [{date}] Sin registros en Daily_Performance")

# -- 3. Verificar measurements -------------------------------------------------
print(f"\n{'-'*60}")
print("MEASUREMENTS (App Movil) - Lo que enviaron los deportistas:")

to_recover = []

for athlete in athletes:
    for date in dates:
        meas = list(
            db.collection('athletes').document(athlete['id'])
              .collection('measurements')
              .where('date', '==', date)
              .order_by('timestamp', direction=firestore.Query.DESCENDING)
              .limit(1)
              .stream()
        )

        key = f"{athlete['id']}_{date}"

        if meas:
            m = meas[0].to_dict()
            iri = m.get('iri', '?')
            sync_method = m.get('sync_method', '?')
            in_dp = key in dp_existing
            status = "[OK - EN DASHBOARD]" if in_dp else "[FALTA EN DASHBOARD]"
            print(f"   {status} [{date}] {athlete['name']} | IRI: {iri} | metodo: {sync_method}")
            if not in_dp:
                to_recover.append((athlete['id'], athlete['name'], date, m))
        else:
            print(f"   [SIN DATOS] [{date}] {athlete['name']} | Sin medicion en app")

# -- 4. Recuperar los que faltan -----------------------------------------------
print(f"\n{'-'*60}")
if not to_recover:
    print("[OK] Todos los datos estan sincronizados. No hay nada que recuperar.")
else:
    print(f"[RECOVER] Recuperando {len(to_recover)} registro(s) faltante(s)...\n")

    recovered = 0
    failed    = 0

    for (athlete_id, athlete_name, date, m_data) in to_recover:
        try:
            pvt      = m_data.get('pvt', {})
            metrics  = pvt.get('metrics', {})
            mean_lat = metrics.get('meanLatency', m_data.get('latency', 0))

            doc_id  = f"{athlete_id}_{date}"
            payload = {
                'athleteId':   athlete_id,
                'athleteName': athlete_name,
                'date':        date,
                'iri':         m_data.get('iri', 0),
                'status':      m_data.get('status', ''),
                'lapses':      metrics.get('lapses', 0),
                'latency':     mean_lat,
                'wellness':    m_data.get('wellness'),
                'pvt':         pvt,
                'timestamp':   firestore.SERVER_TIMESTAMP,
                'sync_method': 'script_recovery_manual',
            }

            db.collection('Daily_Performance').document(doc_id).set(payload, merge=True)
            print(f"   [RECOVERED] {athlete_name} [{date}] | IRI: {m_data.get('iri','?')}")
            recovered += 1

        except Exception as e:
            print(f"   [ERROR] {athlete_name} [{date}]: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"  RECUPERACION COMPLETADA")
    print(f"  Sincronizados : {recovered}")
    print(f"  Fallos        : {failed}")
    print(f"{'='*60}")
    print("\n>> El listener del dashboard actualizara la vista automaticamente.")

print()
