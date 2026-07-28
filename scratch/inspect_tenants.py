import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import firebase_admin
from firebase_admin import credentials, firestore, auth

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

print("=" * 60)
print("  TENANTS / USUARIOS EN FIRESTORE / AUTH")
print("=" * 60)
try:
    users = auth.list_users().users
    for u in users:
        claims = u.custom_claims or {}
        print(f"User: {u.email} (UID: {u.uid}) | Claims: {claims}")
except Exception as e:
    print(f"Error listando usuarios Auth: {e}")

print("\nColección 'tenants' (o similar si existe):")
for col_name in ['tenants', 'organizations', 'teams', 'users']:
    docs = list(db.collection(col_name).get())
    if docs:
        print(f"--- {col_name} ---")
        for d in docs:
            print(f"  ID: {d.id} | Data: {d.to_dict()}")

print("\n" + "=" * 60)
print("  ATLETAS Y SUS TENANTS")
print("=" * 60)
athletes = db.collection('athletes').get()
tenant_map = {}
for a in athletes:
    data = a.to_dict()
    t = data.get('tenantId', 'SIN_TENANT')
    name = f"{data.get('firstName', '')} {data.get('lastName', '')}".strip() or a.id
    tenant_map.setdefault(t, []).append((a.id, name))

for t, ath_list in tenant_map.items():
    print(f"\nTENANT: '{t}' ({len(ath_list)} atletas)")
    for aid, aname in ath_list:
        print(f"  - {aname} ({aid})")

print("\n" + "=" * 60)
print("  DAILY_PERFORMANCE POR TENANT")
print("=" * 60)
dp_docs = db.collection('Daily_Performance').get()
dp_tenant_map = {}
for dp in dp_docs:
    d = dp.to_dict()
    t = d.get('tenantId', 'SIN_TENANT')
    dp_tenant_map[t] = dp_tenant_map.get(t, 0) + 1

for t, count in dp_tenant_map.items():
    print(f"TENANT: '{t}' -> {count} registros en Daily_Performance")
