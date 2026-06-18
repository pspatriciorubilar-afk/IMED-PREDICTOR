"""
List all Firebase Auth users to find the admin account.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))
from firebase_admin import credentials, initialize_app, auth

# Set up credentials
cred_path = os.path.join(os.path.dirname(__file__), '..', 'app-imed-sport-firebase-adminsdk-v4m2w-81f1853ec7.json')
if not os.path.exists(cred_path):
    print("Service account key not found at expected path")
    sys.exit(1)

cred = credentials.Certificate(cred_path)
try:
    initialize_app(cred)
except ValueError:
    pass # App already initialized

users = []
page = auth.list_users()
while page:
    for user in page.users:
        users.append({
            "uid": user.uid,
            "email": user.email,
            "claims": user.custom_claims
        })
    page = page.get_next_page()

for u in users:
    print(f"Email: {u['email']} | Claims: {u['claims']}")
