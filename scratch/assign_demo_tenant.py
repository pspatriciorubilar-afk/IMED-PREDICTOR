import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

print("=== ASSIGNING DEMO_TENANT TO ALL ATHLETES ===")
athletes = db.collection('athletes').get()
for a in athletes:
    a.reference.update({"tenantId": "demo_tenant"})
    print(f"Updated athlete: {a.id}")

print("\n=== ASSIGNING DEMO_TENANT TO ALL DAILY_PERFORMANCE RECORDS ===")
dp_docs = db.collection('Daily_Performance').get()
updated_dp = 0
for dp in dp_docs:
    dp.reference.update({"tenantId": "demo_tenant"})
    updated_dp += 1
print(f"Updated {updated_dp} Daily_Performance documents.")

print("\n✅ Migration complete! All players and metrics are now assigned to 'demo_tenant'.")
