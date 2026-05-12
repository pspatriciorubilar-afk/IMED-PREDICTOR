import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("c:/Users/Pato/Desktop/proyectos/IMED PREDICTOR/service-account.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Dump last 3 measurements of an athlete to see field names
print("\n--- MEASUREMENTS DUMP ---")
athletes = db.collection("athletes").limit(5).get()
for a in athletes:
    print(f"\nAthlete: {a.id}")
    ms = db.collection("athletes").document(a.id).collection("measurements").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
    for m in ms:
        print(f"Doc: {m.id}")
        print(m.to_dict())
