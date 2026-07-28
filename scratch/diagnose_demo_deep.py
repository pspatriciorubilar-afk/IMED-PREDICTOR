import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

print("=" * 70)
print("  DIAGNÓSTICO PROFUNDO — CUENTA DEMO (demo_tenant)")
print("=" * 70)

# 1. Verificar atletas bajo demo_tenant
print("\n[1] Atletas con tenantId='demo_tenant':")
athletes = list(db.collection('athletes').where('tenantId', '==', 'demo_tenant').get())
print(f"  Total atletas: {len(athletes)}")
for a in athletes:
    d = a.to_dict()
    print(f"  - {a.id} | {d.get('firstName','')} {d.get('lastName','')} | tenantId={d.get('tenantId')}")

# 2. Verificar Daily_Performance bajo demo_tenant
print("\n[2] Daily_Performance con tenantId='demo_tenant' (primeros 15):")
dp_docs = list(db.collection('Daily_Performance').where('tenantId', '==', 'demo_tenant').limit(15).get())
print(f"  Total encontrados (limit 15): {len(dp_docs)}")
for dp in dp_docs:
    d = dp.to_dict()
    aa = d.get('advanced_analysis') or {}
    print(f"  ID: {dp.id}")
    print(f"    athleteId: {d.get('athleteId')} | date: {d.get('date')} | iri: {d.get('iri')}")
    print(f"    tenantId:  {d.get('tenantId')}")
    print(f"    adv_analysis keys: {list(aa.keys()) if aa else 'NONE/EMPTY'}")
    print(f"    pvt keys: {list(d.get('pvt',{}).keys())}")
    print()

# 3. Total conteo
print(f"\n[3] Total Daily_Performance con demo_tenant:")
total = list(db.collection('Daily_Performance').where('tenantId', '==', 'demo_tenant').get())
print(f"  Conteo real: {len(total)}")

# 4. Sample de 1 documento completo para Diego
print("\n[4] Documento completo de Daily_Performance para Diego:")
diego_docs = [dp for dp in total if 'diego' in str(dp.to_dict().get('athleteId','')).lower()]
if diego_docs:
    diego_docs.sort(key=lambda d: d.to_dict().get('date',''), reverse=True)
    d = diego_docs[0].to_dict()
    print(f"  Doc ID: {diego_docs[0].id}")
    for k, v in d.items():
        if k not in ['pvt']:  # pvt puede ser muy largo
            print(f"    {k}: {v}")
    pvt = d.get('pvt', {})
    print(f"  pvt.keys: {list(pvt.keys())}")
    metrics = pvt.get('metrics', {})
    print(f"  pvt.metrics.keys: {list(metrics.keys())}")
else:
    print("  NO SE ENCONTRARON REGISTROS PARA DIEGO")
