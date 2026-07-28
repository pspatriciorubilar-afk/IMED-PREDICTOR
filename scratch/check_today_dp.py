import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Check today's document for Patricio Rubilar in Daily_Performance
doc = db.collection('Daily_Performance').document('patricio_rubilar_45_2026-07-23').get()
if doc.exists:
    print("Daily_Performance doc for today:", doc.to_dict())
else:
    print("No Daily_Performance doc found for today.")
