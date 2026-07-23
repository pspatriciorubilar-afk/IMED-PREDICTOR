import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'functions'))
import firebase_admin
from firebase_admin import credentials, auth

SA_PATH = os.path.join(os.path.dirname(__file__), '..', 'functions', 'serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(SA_PATH))

email = "demo@imedpredictor.com"

user = auth.get_user_by_email(email)
auth.update_user(user.uid, password="ImedDemo2026!", disabled=False)
auth.set_custom_user_claims(user.uid, {'role': 'DEMO'})
print(f"Demo account confirmed:")
print(f"  Email   : demo@imedpredictor.com")
print(f"  Password: ImedDemo2026!")
print(f"  Role    : DEMO")
print(f"  Status  : ENABLED")
