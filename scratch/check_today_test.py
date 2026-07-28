import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

print("=== CHECKING ALL ATHLETES AND THEIR MEASUREMENTS ===")
athletes = db.collection('athletes').get()
print(f"Total athletes found: {len(athletes)}")

for a in athletes:
    aid = a.id
    adata = a.to_dict()
    name = adata.get('fullName') or (str(adata.get('firstName', '')) + ' ' + str(adata.get('lastName', ''))).strip() or aid
    
    # Check measurements subcollection
    m_docs = db.collection('athletes').document(aid).collection('measurements').get()
    
    if m_docs:
        print(f"\nAthlete: {name} (ID: {aid}) - Total measurements: {len(m_docs)}")
        # Sort manually by timestamp / date
        sorted_m = sorted(m_docs, key=lambda x: str(x.to_dict().get('timestamp', '') or x.to_dict().get('date', '')), reverse=True)[:3]
        for m in sorted_m:
            mdata = m.to_dict()
            ts = mdata.get('timestamp')
            date = mdata.get('date')
            print(f"   Measurement ID: {m.id} | Date: {date} | TS: {ts} | IRI: {mdata.get('iri')}")

print("\n=== CHECKING DAILY_PERFORMANCE FOR TODAY (2026-07-23) ===")
dp_today = db.collection('Daily_Performance').where('date', '==', '2026-07-23').get()
print(f"Daily_Performance docs for 2026-07-23: {len(dp_today)}")
for dp in dp_today:
    print(f"   DP ID: {dp.id} | Data: {dp.to_dict()}")
