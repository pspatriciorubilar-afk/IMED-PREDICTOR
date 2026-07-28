import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

print("=== SEARCHING FOR DIEGO ===")
athletes = db.collection('athletes').get()
diego_id = None
diego_name = ""
for a in athletes:
    data = a.to_dict()
    name = f"{data.get('firstName', '')} {data.get('lastName', '')}".strip()
    if 'diego' in name.lower():
        diego_id = a.id
        diego_name = name
        print(f"Found: ID={a.id}, Name={name}, Tenant={data.get('tenantId')}")

if not diego_id:
    print("Diego not found in 'athletes'. Checking all athletes:")
    for a in athletes:
        data = a.to_dict()
        print(f"ID={a.id}, Name={data.get('firstName')} {data.get('lastName')}")
else:
    print(f"\n--- DAILY PERFORMANCE FOR {diego_name} ({diego_id}) ---")
    dp_docs = db.collection('Daily_Performance').where('athleteId', '==', diego_id).get()
    for d in sorted(dp_docs, key=lambda x: x.to_dict().get('date', ''), reverse=True):
        dd = d.to_dict()
        print(f"Date: {dd.get('date')} | IRI: {dd.get('iri')} | advanced_analysis: {dd.get('advanced_analysis')}")
        
    print(f"\n--- RAW MEASUREMENTS FOR {diego_name} ({diego_id}) ---")
    m_docs = db.collection('athletes').document(diego_id).collection('measurements').get()
    for m in sorted(m_docs, key=lambda x: x.id, reverse=True):
        md = m.to_dict()
        pvt = md.get('pvt', {})
        metrics = pvt.get('metrics', {})
        trials = (
            metrics.get("trials") or
            metrics.get("rawReactionTimes") or
            pvt.get("trials") or
            pvt.get("logs") or
            md.get("trials") or
            []
        )
        print(f"Date: {m.id} | Trials count: {len(trials)} | Sample trials: {trials[:3] if trials else 'NONE'}")
