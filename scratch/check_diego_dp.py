import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))
import firebase_admin
from firebase_admin import credentials, firestore

SA_PATH = os.path.join(os.path.dirname(__file__), '..', 'functions', 'serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(SA_PATH))

db = firestore.client()

dp = list(db.collection('Daily_Performance').stream())
print("All Daily_Performance containing diego:")
for doc in dp:
    d = doc.to_dict()
    aid = d.get('athleteId', '')
    name = d.get('athleteName', '')
    if 'diego' in aid.lower() or 'diego' in name.lower() or 'da' in aid or 'da' in name:
        print(f"ID: {doc.id} | athleteId: {aid} | athleteName: {name}")

print("\nAll athletes containing diego:")
athletes = list(db.collection('athletes').stream())
for a in athletes:
    d = a.to_dict()
    first = d.get('firstName', '')
    last = d.get('lastName', '')
    full = f"{first} {last}"
    if 'diego' in a.id.lower() or 'diego' in full.lower():
        print(f"ID: {a.id} | Name: {full}")
