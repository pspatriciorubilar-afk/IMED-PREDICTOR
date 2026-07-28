import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

print("=== LISTING ALL USERS IN FIREBASE AUTH ===")
page = auth.list_users()
while page:
    for user in page.users:
        print(f"UID: {user.uid} | Email: {user.email} | DisplayName: {user.display_name} | CustomClaims: {user.custom_claims}")
    page = page.get_next_page()
