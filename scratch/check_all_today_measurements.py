import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

print("=== CHECKING ALL MEASUREMENTS IN SYSTEM CREATED TODAY ===")
athletes = db.collection('athletes').get()
for a in athletes:
    m_docs = db.collection('athletes').document(a.id).collection('measurements').get()
    for m in m_docs:
        mdata = m.to_dict()
        ts = mdata.get('timestamp', '')
        # check if ts contains 2026-07-23 or 2026-07-24 (depending on timezone)
        if isinstance(ts, str) and ('2026-07-23' in ts or '2026-07-24' in ts):
            print(f"Athlete: {a.id} | Measurement ID: {m.id} | Timestamp: {ts} | IRI: {mdata.get('iri')} | Status: {mdata.get('status')}")
