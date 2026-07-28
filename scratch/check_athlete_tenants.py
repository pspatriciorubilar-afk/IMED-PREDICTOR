import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

print("=== ATHLETE TENANTS IN FIRESTORE ===")
athletes = db.collection('athletes').get()
for a in athletes:
    data = a.to_dict()
    print(f"ID: {a.id} | Name: {data.get('firstName')} {data.get('lastName')} | TenantId: {data.get('tenantId')}")
