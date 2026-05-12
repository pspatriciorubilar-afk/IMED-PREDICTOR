import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar con el proyecto real
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

print("🔍 Buscando deportistas en la colección 'athletes'...")
docs = db.collection("athletes").limit(10).get()

if not docs:
    print("❌ No se encontraron documentos en la colección 'athletes'.")
else:
    print(f"✅ Se encontraron {len(docs)} deportistas:")
    for doc in docs:
        d = doc.to_dict()
        name = f"{d.get('firstName', '')} {d.get('lastName', '')}".strip() or d.get('name', 'Sin nombre')
        print(f" - ID: {doc.id} | Nombre: {name} | Posición: {d.get('position', 'N/A')}")
