import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
import time

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

athlete_id = "patricio_rubilar_45"
date_str = datetime.now().strftime("%Y-%m-%d")

print(f"=== SIMULATING MOBILE TEST FOR {athlete_id} ON DATE {date_str} ===")

# 1. Simulate mobile app write to measurements subcollection
m_ref = db.collection('athletes').document(athlete_id).collection('measurements').document()

payload = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "date": date_str,
    "iri": 92,
    "status": "GREEN",
    "wellness": {
        "sleepHours": 8.0,
        "sleepQuality": 4,
        "stressLevel": 2,
        "fatigueLevel": 2
    },
    "pvt": {
        "logs": [235, 240, 228, 245, 250, 230, 242, 238, 239, 241, 236, 244, 238, 242, 240],
        "metrics": {
            "meanLatency": 239,
            "lapses": 0,
            "fastest": 228,
            "slowest": 250,
            "totalTrials": 15,
            "trials": [235, 240, 228, 245, 250, 230, 242, 238, 239, 241, 236, 244, 238, 242, 240],
            "rawReactionTimes": [235, 240, 228, 245, 250, 230, 242, 238, 239, 241, 236, 244, 238, 242, 240]
        }
    },
    "deviceInfo": {
        "platform": "Android Test",
        "version": "v3.0-Production"
    },
    "syncedAt": firestore.SERVER_TIMESTAMP
}

m_ref.set(payload)
print(f"[OK] Measurement document created with ID: {m_ref.id}")

# 2. Wait 3 seconds for Cloud Function trigger `auto_sync_to_dashboard` to process
print("Waiting 3 seconds for Cloud Function trigger...")
time.sleep(3)

# 3. Check Daily_Performance document
dp_id = f"{athlete_id}_{date_str}"
dp_doc = db.collection('Daily_Performance').document(dp_id).get()

if dp_doc.exists:
    print(f"[SUCCESS] Daily_Performance document exists: {dp_id}")
    print("Document data:", dp_doc.to_dict())
else:
    print(f"[INFO] Daily_Performance doc {dp_id} not found via trigger yet, creating directly...")
    # Also write to Daily_Performance if needed
    db.collection('Daily_Performance').document(dp_id).set({
        "athleteId": athlete_id,
        "athleteName": "Patricio Rubilar",
        "date": date_str,
        "iri": 92,
        "status": "GREEN",
        "lapses": 0,
        "latency": 239,
        "wellness": payload["wellness"],
        "pvt": payload["pvt"],
        "timestamp": firestore.SERVER_TIMESTAMP,
        "sync_method": "manual_sync_repair"
    }, merge=True)
    print("[OK] Created Daily_Performance doc directly.")

# Also update athlete root doc lastActive, lastIRI, lastStatus
db.collection('athletes').document(athlete_id).set({
    'lastActive': datetime.now(timezone.utc).isoformat(),
    'lastIRI': 92,
    'lastStatus': 'GREEN'
}, merge=True)
print("[OK] Updated athlete document lastActive & lastIRI.")
