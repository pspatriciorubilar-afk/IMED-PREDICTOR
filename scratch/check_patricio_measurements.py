import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

athlete_id = "patricio_rubilar_45"
print("=== CHECKING ALL MEASUREMENTS FOR PATRICIO ===")
m_docs = db.collection('athletes').document(athlete_id).collection('measurements').get()
for m in sorted(m_docs, key=lambda x: str(x.to_dict().get('timestamp', '')), reverse=True)[:5]:
    mdata = m.to_dict()
    print(f"ID: {m.id} | Timestamp: {mdata.get('timestamp')} | IRI: {mdata.get('iri')} | Status: {mdata.get('status')}")
