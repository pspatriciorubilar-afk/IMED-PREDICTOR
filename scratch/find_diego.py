"""
Busca el athleteId de Diego Dañobeytia en Firestore y muestra
sus measurements duplicados por fecha.
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))

import firebase_admin
from firebase_admin import credentials, firestore

SA_PATH = os.path.join(os.path.dirname(__file__), '..', 'functions', 'serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(SA_PATH))

db = firestore.client()

print("\n" + "="*60)
print("  Búsqueda de Diego Dañobeytia en Firestore")
print("="*60 + "\n")

# 1. Buscar en colección athletes
athletes = list(db.collection('athletes').stream())
diego_id = None

for adoc in athletes:
    ad = adoc.to_dict()
    first = (ad.get('firstName') or '').lower()
    last  = (ad.get('lastName')  or '').lower()
    full  = f"{first} {last}"

    if 'diego' in full or 'danobeytia' in full or 'dañobeytia' in full or 'da' in last:
        print(f"✅ ENCONTRADO: {ad.get('firstName')} {ad.get('lastName')}")
        print(f"   athleteId : {adoc.id}")
        print(f"   lastIRI   : {ad.get('lastIRI', '?')}")
        print(f"   lastStatus: {ad.get('lastStatus', '?')}")
        diego_id = adoc.id
        print()

if not diego_id:
    # Buscar más amplio — mostrar TODOS los atletas
    print("❌ No encontrado directamente. Listando TODOS los atletas:\n")
    for adoc in athletes:
        ad = adoc.to_dict()
        name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip()
        print(f"   [{adoc.id}] {name}")
    sys.exit(0)

# 2. Analizar measurements duplicados por fecha
print("\n" + "-"*60)
print(f"  Measurements de Diego ({diego_id})")
print("-"*60 + "\n")

m_docs = list(db.collection('athletes').document(diego_id).collection('measurements').stream())
print(f"Total de measurements encontrados: {len(m_docs)}\n")

# Agrupar por fecha
by_date = {}
for doc in m_docs:
    data = doc.to_dict()
    raw_ts   = data.get('timestamp', '')
    date_str = data.get('date') or (raw_ts[:10] if isinstance(raw_ts, str) and len(raw_ts) >= 10 else 'sin_fecha')
    iri      = data.get('iri', 0) or 0
    sync     = data.get('sync_method', '?')

    if date_str not in by_date:
        by_date[date_str] = []
    by_date[date_str].append({'id': doc.id, 'iri': iri, 'sync': sync})

for date_str, docs in sorted(by_date.items()):
    dup_flag = " ⚠️  DUPLICADO" if len(docs) > 1 else ""
    print(f"  📅 {date_str} — {len(docs)} registro(s){dup_flag}")
    for d in docs:
        print(f"     └─ [{d['id']}] IRI={d['iri']} | sync={d['sync']}")

# 3. Revisar Daily_Performance para Diego
print("\n" + "-"*60)
print(f"  Daily_Performance de Diego")
print("-"*60 + "\n")

dp_docs = list(db.collection('Daily_Performance').where('athleteId', '==', diego_id).stream())
print(f"Total documentos en Daily_Performance: {len(dp_docs)}\n")
for doc in dp_docs:
    d = doc.to_dict()
    print(f"  📄 {doc.id} | date={d.get('date','?')} | IRI={d.get('iri','?')} | sync={d.get('sync_method','?')}")

print("\n✅ Análisis completo. Copia el athleteId para ejecutar la limpieza.\n")
