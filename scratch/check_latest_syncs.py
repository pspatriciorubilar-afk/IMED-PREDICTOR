import firebase_admin
from firebase_admin import credentials, firestore
import json

cred = credentials.Certificate('functions/serviceAccount.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

print('=== ULTIMOS 15 REGISTROS EN DAILY_PERFORMANCE ===')
docs = db.collection('Daily_Performance').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(15).get()
for d in docs:
    data = d.to_dict()
    ts = data.get('timestamp')
    ts_str = ts.isoformat() if ts else 'NONE'
    print(f"ID: {d.id} | AthleteId: {data.get('athleteId')} | Date: {data.get('date')} | TS: {ts_str} | Source: {data.get('source')}")
