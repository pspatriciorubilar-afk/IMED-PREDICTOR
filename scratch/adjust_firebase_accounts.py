import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

print("=== ADJUSTING FIREBASE AUTH USERS ===")

# 1. Update/Configure ps.patriciorubilar@gmail.com
try:
    user_ps = auth.get_user_by_email("ps.patriciorubilar@gmail.com")
    auth.set_custom_user_claims(user_ps.uid, {"role": "SUPER_ADMIN"})
    print(f"[OK] Configured ps.patriciorubilar@gmail.com as SUPER_ADMIN (UID: {user_ps.uid})")
except Exception as e:
    print(f"[ERROR] Could not configure ps.patriciorubilar@gmail.com: {e}")

# 2. Update/Configure demo@imedpredictor.com
try:
    user_demo = auth.get_user_by_email("demo@imedpredictor.com")
    auth.set_custom_user_claims(user_demo.uid, {"role": "DEMO"})
    print(f"[OK] Configured demo@imedpredictor.com as DEMO (UID: {user_demo.uid})")
except Exception as e:
    print(f"[ERROR] Could not configure demo@imedpredictor.com: {e}")

# 3. Delete admin@imedpredictor.com
try:
    user_admin = auth.get_user_by_email("admin@imedpredictor.com")
    auth.delete_user(user_admin.uid)
    print(f"[OK] Deleted admin@imedpredictor.com (UID: {user_admin.uid})")
except Exception as e:
    print(f"[INFO] admin@imedpredictor.com not found or already deleted: {e}")

# 4. Delete errubi22@hotmail.com
try:
    user_coach = auth.get_user_by_email("errubi22@hotmail.com")
    auth.delete_user(user_coach.uid)
    print(f"[OK] Deleted errubi22@hotmail.com (UID: {user_coach.uid})")
except Exception as e:
    print(f"[INFO] errubi22@hotmail.com not found or already deleted: {e}")

print("=== FINISHED USERS ADJUSTMENT ===")
