import sys
import os
import io

# Configurar stdout y stderr en utf-8 para evitar errores de codificación en Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import firebase_admin
from firebase_admin import credentials, firestore

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions'))
import pvt_exgauss_worker as worker

cred = credentials.Certificate('functions/serviceAccount.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

print("=" * 70)
print("  REPROCESO MASIVO EX-GAUSSIANO Y Z-SCORES (CRONOLÓGICO)")
print("=" * 70)

athletes_snap = db.collection('athletes').get()
total_athletes = 0
total_measurements = 0

for ath_doc in athletes_snap:
    athlete_id = ath_doc.id
    ath_data = ath_doc.to_dict()
    ath_name = f"{ath_data.get('firstName', '')} {ath_data.get('lastName', '')}".strip() or athlete_id
    
    # Consultar mediciones del atleta en orden ASCENDENTE por fecha
    m_docs = db.collection('athletes').document(athlete_id).collection('measurements').get()
    
    if not m_docs:
        continue

    # Ordenar cronológicamente ascendente para construir correctamente el historial para Z-Score
    sorted_m = sorted(m_docs, key=lambda x: (x.to_dict().get("date") or x.id))
    
    has_trials = False
    print(f"\nAthleta: {ath_name} ({athlete_id}) -- {len(sorted_m)} mediciones encontradas")
    
    for m_doc in sorted_m:
        md = m_doc.to_dict()
        raw_ts = md.get("timestamp", "")
        date_str = md.get("date") or (raw_ts[:10] if isinstance(raw_ts, str) and len(raw_ts) >= 10 else m_doc.id)
        if not date_str or len(date_str) != 10:
            continue
            
        pvt = md.get("pvt", {})
        metrics = pvt.get("metrics", {})
        trials = (
            metrics.get("trials") or
            metrics.get("rawReactionTimes") or
            pvt.get("trials") or
            pvt.get("logs") or
            md.get("trials") or
            []
        )
        
        valid_trials = [float(t) for t in trials if isinstance(t, (int, float))]
        if valid_trials and len(valid_trials) >= 20:
            has_trials = True
            payload = {
                "athlete_id": athlete_id,
                "athlete_name": ath_name,
                "date": date_str,
                "trials": valid_trials,
                "wellness": md.get("wellness"),
                "iri": md.get("iri")
            }
            try:
                worker.process_athlete(db, payload, date_str)
                total_measurements += 1
            except Exception as e:
                print(f"  [Error] procesando {date_str} para {ath_name}: {e}")
        else:
            print(f"  [Aviso] {date_str}: Sin suficientes trials ({len(valid_trials)}). Saltando Ex-Gauss.")
            
    if has_trials:
        total_athletes += 1

print("\n" + "=" * 70)
print(f"COMPLETADO: {total_measurements} mediciones analizadas en {total_athletes} atletas.")
print("=" * 70)
