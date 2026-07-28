import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

athlete_id = "patricio_rubilar_45"
date_str = "2026-07-23"

print("=== UPDATING TODAY'S FIRESTORE DOCUMENTS TO IRI 89 ===")

# 1. Update Daily_Performance
dp_ref = db.collection('Daily_Performance').document(f"{athlete_id}_{date_str}")
if dp_ref.get().exists:
    dp_ref.update({
        "iri": 89,
        "pvt.metrics.iri": 89
    })
    print("[OK] Updated Daily_Performance to IRI 89")

# 2. Update all measurements for today in athletes collection
m_docs = db.collection('athletes').document(athlete_id).collection('measurements').get()
for m in m_docs:
    mdata = m.to_dict()
    ts = mdata.get('timestamp', '')
    if isinstance(ts, str) and date_str in ts:
        m.reference.update({
            "iri": 89
        })
        print(f"[OK] Updated measurement doc {m.id} to IRI 89")

# 3. Update athlete root document
db.collection('athletes').document(athlete_id).update({
    "lastIRI": 89
})
print("[OK] Updated athlete root doc to lastIRI 89")
