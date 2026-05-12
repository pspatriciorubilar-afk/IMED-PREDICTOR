import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

print("🔍 Listando colecciones raíz...")
collections = db.collections()
for coll in collections:
    print(f" - Colección hallada: {coll.id}")
    # Ver si tiene documentos
    docs = coll.limit(1).get()
    if docs:
        print(f"   (Tiene documentos)")
    else:
        print(f"   (Vacía)")
