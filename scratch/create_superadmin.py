import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))
import firebase_admin
from firebase_admin import credentials, initialize_app, auth

SA_PATH = os.path.join(os.path.dirname(__file__), '..', 'functions', 'serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(SA_PATH))

email = "admin@imedpredictor.com"
password = "imedadmin2026"

try:
    user = auth.create_user(email=email, password=password)
    auth.set_custom_user_claims(user.uid, {'role': 'ADMIN'})
    print(f"Created {email}")
except auth.EmailAlreadyExistsError:
    user = auth.get_user_by_email(email)
    auth.update_user(user.uid, password=password)
    auth.set_custom_user_claims(user.uid, {'role': 'ADMIN'})
    print(f"Updated {email}")
