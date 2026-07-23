import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

cred = credentials.Certificate('functions/serviceAccount.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

athlete_id = "diego_daobeytia_16" # Usamos el ID con el caracter especial para asegurar coincidencia exacta
# Tambien intentamos con el ID limpio si existe
alternate_id = "diego_dañobeytia_16"

for aid in [athlete_id, alternate_id]:
    print(f"\n=== INSPECCIONANDO SUBCOLECCION MEASUREMENTS PARA: {aid} ===")
    ref = db.collection('athletes').document(aid).collection('measurements')
    docs = ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5).get()
    
    if not docs:
        print("No se encontraron mediciones bajo este ID o el documento no existe.")
        continue
        
    for d in docs:
        data = d.to_dict()
        ts = data.get('timestamp')
        ts_str = ts if isinstance(ts, str) else (ts.isoformat() if ts else 'NONE')
        print(f"Doc ID: {d.id} | Date: {data.get('date')} | TS: {ts_str} | Completed: {data.get('completed')}")
