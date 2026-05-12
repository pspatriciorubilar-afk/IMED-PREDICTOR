import firebase_admin
from firebase_admin import firestore
import os

# Usar credenciales por defecto de la máquina (si está logueado en gcloud/firebase)
firebase_admin.initialize_app()
db = firestore.client()

print("\n=== AUDITORÍA DE DATOS FIRESTORE (app-imed-sport) ===")

# 1. Verificar últimos registros en Daily_Performance
print("\n--- ÚLTIMOS 5 EN Daily_Performance ---")
docs = db.collection("Daily_Performance").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5).get()
if not docs:
    print("No hay registros en Daily_Performance.")
for d in docs:
    data = d.to_dict()
    print(f"ID: {d.id:30} | Date: {data.get('date')} | Athlete: {data.get('athleteName','?'):20} | IRI: {data.get('iri')} | GPS: {'SÍ' if 'gps' in data else 'NO'}")

# 2. Verificar si hay algo para HOY
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")
print(f"\n--- BUSCANDO REGISTROS DE HOY ({today}) ---")
today_docs = db.collection("Daily_Performance").where("date", "==", today).get()
print(f"Total encontrados hoy: {len(today_docs)}")
for d in today_docs:
    print(f"- {d.id}")

# 3. Verificar subcolección measurements de un atleta activo
if docs:
    sample_id = docs[0].to_dict().get("athleteId")
    if sample_id:
        print(f"\n--- ÚLTIMAS MEDICIONES PARA {sample_id} ---")
        m_docs = db.collection("athletes").document(sample_id).collection("measurements").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(3).get()
        for m in m_docs:
            mdata = m.to_dict()
            print(f"  Doc: {m.id[:10]}... | Date: {mdata.get('date')} | IRI: {mdata.get('iri')}")
