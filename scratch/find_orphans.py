"""
Busqueda de datos huerfanos de hoy en Daily_Performance.
Detecta registros con athleteId = athlete_pending_xxx y los reasigna.
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
today = datetime.now().strftime('%Y-%m-%d')

print(f"\n{'='*60}")
print(f"  Busqueda de registros huerfanos - {today}")
print(f"{'='*60}\n")

# -- 1. Buscar TODOS los Daily_Performance de hoy sin filtro de athleteId ------
print(">> TODOS los documentos Daily_Performance de hoy:\n")
all_today = list(db.collection('Daily_Performance').where('date', '==', today).stream())
if not all_today:
    print("   [VACIO] No hay ningun documento con date == hoy.")
else:
    for doc in all_today:
        d = doc.to_dict()
        aid = d.get('athleteId', '?')
        flag = " <<< HUERFANO (pendiente)" if str(aid).startswith('athlete_pending_') else ""
        print(f"   Doc: {doc.id}")
        print(f"   athleteId   : {aid}{flag}")
        print(f"   athleteName : {d.get('athleteName','?')}")
        print(f"   IRI         : {d.get('iri','?')}")
        print(f"   sync_method : {d.get('sync_method','?')}")
        print()

# -- 2. Buscar measurements con timestamp >= hoy 00:00 (por si date es erroneo)
print(f"\n>> Measurements con timestamp de hoy en toda la coleccion athletes:\n")

athletes_docs = list(db.collection('athletes').stream())
found_any = False
for adoc in athletes_docs:
    ad = adoc.to_dict()
    name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip() or adoc.id
    meas = list(
        db.collection('athletes').document(adoc.id)
          .collection('measurements')
          .order_by('timestamp', direction=firestore.Query.DESCENDING)
          .limit(3)
          .stream()
    )
    for m in meas:
        md = m.to_dict()
        ts = str(md.get('timestamp', ''))
        date_field = md.get('date', '')
        if ts[:10] == today or date_field == today:
            found_any = True
            print(f"   [{name}] (ID: {adoc.id})")
            print(f"   measurement_id : {m.id}")
            print(f"   date           : {date_field}")
            print(f"   timestamp      : {ts[:19]}")
            print(f"   IRI            : {md.get('iri','?')}")
            print()

if not found_any:
    print("   [NINGUNO] No hay measurements con timestamp de hoy en ninguna subcolecion.")

# -- 3. Buscar en Daily_Performance por timestamp de hoy (sin importar date) ---
print(f"\n>> Daily_Performance por timestamp de hoy (sin filtro de date):\n")

# Usar rango de timestamps de hoy
from google.cloud.firestore_v1.base_query import FieldFilter
today_start = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 0, 0)
today_end   = today_start + timedelta(days=1)

# Buscar por string timestamp (como guarda Flutter)
all_dp = list(db.collection('Daily_Performance').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(20).stream())
print(f"   Ultimos 20 docs en Daily_Performance:\n")
for doc in all_dp:
    d = doc.to_dict()
    ts = d.get('timestamp')
    date_f = d.get('date', '?')
    aid = d.get('athleteId', '?')
    name = d.get('athleteName', '?')
    # Detectar si es de hoy por servidor timestamp o por date
    is_today = date_f == today
    marker = " <<< HOY" if is_today else ""
    pending_marker = " <<< HUERFANO" if str(aid).startswith('athlete_pending_') else ""
    print(f"   {doc.id}: date={date_f} | athlete={name} | IRI={d.get('iri','?')}{marker}{pending_marker}")

print()
