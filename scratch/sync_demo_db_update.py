import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import firebase_admin
from firebase_admin import credentials, firestore, auth

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

print("=" * 70)
print("  ACTUALIZACIÓN Y SINCRONIZACIÓN DE LA BASE DE DATOS PARA CUENTA DEMO")
print("  (Postulacion Semilla CORFO -- Cuenta: demo@imedpredictor.com)")
print("=" * 70)

# 1. Asegurar custom claims del usuario demo en Auth
try:
    demo_user = auth.get_user_by_email("demo@imedpredictor.com")
    claims = demo_user.custom_claims or {}
    claims.update({"role": "DEMO", "tenantId": "demo_tenant"})
    auth.set_custom_user_claims(demo_user.uid, claims)
    print(f"✅ Auth custom claims confirmadas para {demo_user.email}: {claims}")
except Exception as e:
    print(f"⚠️ Aviso en Auth demo user: {e}")

# 2. Actualizar todos los deportistas a 'demo_tenant'
print("\n--- 1. Asignando 'demo_tenant' a todos los atletas actuales ---")
athletes = list(db.collection("athletes").get())
ath_count = 0
for a in athletes:
    data = a.to_dict()
    name = f"{data.get('firstName', '')} {data.get('lastName', '')}".strip() or a.id
    a.reference.update({"tenantId": "demo_tenant"})
    ath_count += 1
    print(f"  -> Atleta alineado a demo_tenant: {name} ({a.id})")
print(f"Total atletas alineados: {ath_count}")

# 3. Actualizar subcolección 'measurements' de cada atleta
print("\n--- 2. Asignando 'demo_tenant' a historial crudo (measurements) ---")
meas_count = 0
for a in athletes:
    m_docs = db.collection("athletes").document(a.id).collection("measurements").get()
    for m in m_docs:
        if m.to_dict().get("tenantId") != "demo_tenant":
            m.reference.update({"tenantId": "demo_tenant"})
        meas_count += 1
print(f"Total mediciones crudas alineadas a demo_tenant: {meas_count}")

# 4. Actualizar toda la colección 'Daily_Performance' a 'demo_tenant'
print("\n--- 3. Asignando 'demo_tenant' al Dashboard (Daily_Performance) ---")
dp_docs = list(db.collection("Daily_Performance").get())
dp_count = 0
fixed_dp = 0
for dp in dp_docs:
    d = dp.to_dict()
    if d.get("tenantId") != "demo_tenant":
        dp.reference.update({"tenantId": "demo_tenant"})
        fixed_dp += 1
    dp_count += 1

print(f"Total registros en Daily_Performance: {dp_count} | Reparados sin tenant o cambiados a demo_tenant: {fixed_dp}")

print("\n" + "=" * 70)
print("✅ CARGA Y ALINEACIÓN FINALIZADA CON ÉXITO")
print("La cuenta de demo ahora refleja el 100% de la base de datos actualizada")
print("y con todos los cálculos Ex-Gaussianos de la cuenta principal.")
print("=" * 70)
