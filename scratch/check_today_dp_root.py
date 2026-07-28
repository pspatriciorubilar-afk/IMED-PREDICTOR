import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

doc = db.collection('Daily_Performance').document('patricio_rubilar_45_2026-07-23').get()
if doc.exists:
    d = doc.to_dict()
    print("=== ROOT FIELDS ===")
    print("iri:", d.get("iri"))
    print("lapses:", d.get("lapses"))
    print("latency:", d.get("latency"))
    print("wellness:", d.get("wellness"))
    print("sync_method:", d.get("sync_method"))
else:
    print("No Daily_Performance doc found for today.")
