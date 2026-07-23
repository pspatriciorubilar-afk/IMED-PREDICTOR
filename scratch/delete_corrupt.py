import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))
import firebase_admin
from firebase_admin import credentials, firestore

SA_PATH = os.path.join(os.path.dirname(__file__), '..', 'functions', 'serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(SA_PATH))

db = firestore.client()

athletes = list(db.collection('athletes').stream())
print("All athletes:")
for a in athletes:
    d = a.to_dict()
    first = d.get('firstName', '')
    last = d.get('lastName', '')
    full = f"{first} {last}"
    print(f"ID: {a.id} | Name: {full}")
    if 'Ã' in a.id or 'Ã' in full:
        print(f"FOUND CORRUPT RECORD! ID: {a.id}")
        # Delete measurements
        measurements = list(db.collection('athletes').document(a.id).collection('measurements').stream())
        for m in measurements:
            m.reference.delete()
            print(f"Deleted measurement {m.id} for {a.id}")
        # Delete athlete
        a.reference.delete()
        print(f"Deleted athlete {a.id}")
        
        # Delete from Daily_Performance
        dp = list(db.collection('Daily_Performance').where('athleteId', '==', a.id).stream())
        for doc in dp:
            doc.reference.delete()
            print(f"Deleted daily performance {doc.id} for {a.id}")
