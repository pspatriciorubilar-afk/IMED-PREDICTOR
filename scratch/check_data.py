import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': 'app-imed-sport',
})

db = firestore.client()

print("Listing athletes...")
docs = db.collection('athletes').limit(5).stream()
count = 0
for doc in docs:
    print(f"Found athlete: {doc.id} => {doc.to_dict().get('firstName', 'N/A')}")
    count += 1

if count == 0:
    print("No athletes found!")
else:
    print(f"Total athletes sampled: {count}")
