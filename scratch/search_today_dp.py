import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

print("=== SEARCHING ALL DEPORTISTAS AND THEIR DAILY PERFORMANCE ===")
dp_docs = db.collection('Daily_Performance').get()
for d in dp_docs:
    ddata = d.to_dict()
    date = ddata.get('date', '')
    if '2026-07-23' in date or '2026-07-24' in date:
        print(f"Doc ID: {d.id} | Date: {date} | IRI: {ddata.get('iri')} | AthleteName: {ddata.get('athleteName')} | SyncMethod: {ddata.get('sync_method')}")
