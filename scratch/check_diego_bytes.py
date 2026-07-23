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
    if 'diego' in aid.lower() or 'diego' in name.lower():
        print(f"ID: {repr(doc.id)} | athleteId: {repr(aid)} | athleteName: {repr(name)}")
        if 'Ã' in doc.id or '\\xc3\\x83' in repr(doc.id.encode('utf-8')) or 'Ã±' in aid or 'Ã±' in name:
             print("DELETING this rogue record...")
             doc.reference.delete()
             print("Deleted.")
