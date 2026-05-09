from firebase_functions import https_fn, options
from firebase_admin import initialize_app, firestore

# Configuración global
options.set_global_options(region="us-central1")
initialize_app()

@https_fn.on_call()
def process_gps_csv(req: https_fn.CallableRequest) -> dict:
    """
    Función Callable para procesar un CSV de GPS ya subido a Storage.
    Recibe: { "filePath": "gps/ATH001/2026-05-09/archivo.csv" }
    """
    import pandas as pd
    import io
    from firebase_admin import storage
    
    file_path = req.data.get("filePath")
    if not file_path:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="Falta el filePath."
        )

    print(f"Procesando vía Callable: {file_path}")

    try:
        # 1. Obtener datos del CSV desde Storage
        bucket = storage.bucket() # Usa el bucket por defecto
        blob = bucket.blob(file_path)
        if not blob.exists():
             raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message="El archivo no existe en Storage."
            )
            
        content = blob.download_as_text(encoding="utf-8-sig")
        df = pd.read_csv(io.StringIO(content))
        
        # Mapeo de métricas GPS (Agnóstico)
        gps = {"decel_high": 0.0, "accel_high": 0.0, "max_speed": 0.0}
        cols_map = {
            "decel_high": ["decel_high", "Desaceleraciones Altas", "High Decels", "DecelHigh"],
            "accel_high": ["accel_high", "Aceleraciones Altas", "High Accels", "AccelHigh"],
            "max_speed": ["max_speed", "Velocidad Máxima", "Max Speed", "MaxSpeed"]
        }
        
        for key, aliases in cols_map.items():
            col = next((c for c in df.columns if c.strip() in aliases), None)
            if col:
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                gps[key] = round(float(vals.mean()), 2) if not vals.empty else 0.0

        # 2. Extraer Atleta y Fecha
        # gps/{athleteId}/{date}/...
        parts = file_path.split("/")
        if len(parts) < 3:
             raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Ruta de archivo no válida. Se espera gps/athleteId/date/..."
            )
            
        athlete_id = parts[1]
        date_str = parts[2]
        
        # 3. Consultar disponibilidad neuro (IRI/Lapses) - SOLO LECTURA
        db = firestore.client()
        snap = db.collection("athletes").document(athlete_id).collection("measurements").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
        
        imed = {"iri": 75.0, "lapses": 0}
        if snap:
            m = snap[0].to_dict()
            imed["iri"] = float(m.get("iri", 75))
            imed["lapses"] = int(m.get("pvt", {}).get("metrics", {}).get("lapses", 0))

        # 4. Algoritmo IVN
        risk_level = "GREEN"
        ivn_label = "ADAPTACIÓN ÓPTIMA"
        action = "mantener"
        
        if imed["iri"] < 60 and gps["decel_high"] > 15:
            risk_level, ivn_label, action = "RED", "RIESGO CRÍTICO", "optimizar"
        elif imed["lapses"] > 2:
            risk_level, ivn_label, action = "YELLOW", "RIESGO COORDINACIÓN", "reprogramar"
        elif imed["iri"] < 75:
            risk_level, ivn_label, action = "GREEN", "ESTABLE", "mantener"

        # 5. Guardado en Daily_Performance
        doc_id = f"{athlete_id}_{date_str}"
        payload = {
            "athleteId": athlete_id,
            "date": date_str,
            "gps": gps,
            "iri": imed["iri"],
            "lapses": imed["lapses"],
            "risk_level": risk_level,
            "ivn_label": ivn_label,
            "action": action,
            "processed_at": firestore.SERVER_TIMESTAMP,
            "source": file_path
        }
        
        db.collection("Daily_Performance").document(doc_id).set(payload, merge=True)
        
        return {
            "status": "success",
            "athleteId": athlete_id,
            "riskLevel": risk_level,
            "ivnLabel": ivn_label
        }

    except Exception as e:
        print(f"Error en process_gps_csv: {e}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=str(e)
        )
