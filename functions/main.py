from firebase_functions import https_fn, options
from firebase_admin import initialize_app, firestore

# Configuración global - Rendimiento Optimizado (Plan Blaze)
options.set_global_options(region="us-central1", timeout_sec=60, memory=512)
initialize_app()

@https_fn.on_call()
def process_gps_csv(req: https_fn.CallableRequest) -> dict:
    """
    Motor de Inteligencia IMED Predictor v2.0
    Implementa Algoritmo IVN con ACWR y Análisis de Z5.
    """
    # Importaciones diferidas para evitar timeouts de despliegue
    import pandas as pd
    import io
    import datetime
    from firebase_admin import storage
    
    file_path = req.data.get("filePath")
    if not file_path:
        raise https_fn.HttpsError(https_fn.FunctionsErrorCode.INVALID_ARGUMENT, "Falta el filePath.")

    print(f"[Motor IVN] Iniciando análisis técnico de: {file_path}")

    try:
        # 1. Ingesta Agnóstica del CSV desde Storage
        bucket = storage.bucket()
        blob = bucket.blob(file_path)
        if not blob.exists():
            raise https_fn.HttpsError(https_fn.FunctionsErrorCode.NOT_FOUND, "Archivo no hallado en Storage.")
            
        content = blob.download_as_text(encoding="utf-8-sig")
        df = pd.read_csv(io.StringIO(content))
        
        # ── ADAPTADOR UNIVERSAL INTELIGENTE ──────────────────────────────────
        # Motor de detección semántica en 2 capas:
        # CAPA 1: Si el usuario seleccionó una marca GPS, aplicar sus hints conocidos
        # CAPA 2: Motor semántico puro por puntuación de palabras clave
        # ─────────────────────────────────────────────────────────────────────
        
        gps_brand   = req.data.get("gpsBrand", "auto")
        brand_hints = req.data.get("brandHints", None)  # Dict de listas de columnas por métrica
        
        # Normalizar nombres de columnas
        df.columns = [c.strip() for c in df.columns]
        cols_normalized = {c.lower().replace('_', ' ').replace('-', ' '): c for c in df.columns}
        
        print(f"[GPS Adapter] Marca: '{gps_brand}' | {len(df.columns)} columnas detectadas: {list(df.columns)[:10]}")
        
        # Reglas semánticas por defecto (motor agnóstico)
        semantic_rules = {
            "decel_z5": {
                "must_any": ["decel", "desacel", "fren", "braking", "frena"],
                "boost":    ["high", "alta", "altas", "intense", "z5", "max", "zone 5", "5", "hd", "count", "number", "hi"],
                "exclude":  ["distance", "distancia", "power", "band", "low", "baja"]
            },
            "accel_high": {
                "must_any": ["accel", "acel", "acceleration", "acelerac"],
                "boost":    ["high", "alta", "altas", "intense", "z5", "max", "ha", "count", "number", "hi"],
                "exclude":  ["distance", "distancia", "power", "band", "low", "baja", "decel"]
            },
            "max_speed": {
                "must_any": ["speed", "velocidad", "velocity", "vel "],
                "boost":    ["max", "peak", "top", "maximo", "pico", "highest", "maximum"],
                "exclude":  ["average", "avg", "promedio", "band", "zone", "distance", "relative"]
            },
            "distance": {
                "must_any": ["distance", "distancia", "dist"],
                "boost":    ["total", "covered", "recorrida", "m)", "meters"],
                "exclude":  ["sprint", "high", "band", "zone"]
            },
            "sprint_distance": {
                "must_any": ["sprint", "esprint"],
                "boost":    ["distance", "distancia", "total", "m)"],
                "exclude":  []
            }
        }
        
        def score_column(col_lower: str, rules: dict, brand_col_hints: list = None) -> int:
            """Puntúa una columna. Los hints de marca tienen prioridad máxima."""
            # CAPA 1: Si la columna coincide con un hint específico de la marca → score máximo
            if brand_col_hints:
                for hint in brand_col_hints:
                    if hint.lower().strip() == col_lower.strip():
                        return 100  # Prioridad absoluta
                    if hint.lower().replace('_',' ').replace('-',' ') in col_lower:
                        return 80   # Coincidencia parcial del hint
            
            # CAPA 2: Motor semántico genérico
            for ex in rules.get("exclude", []):
                if ex in col_lower:
                    return -1
            if not any(must in col_lower for must in rules["must_any"]):
                return 0
            score = 1
            for b in rules.get("boost", []):
                if b in col_lower:
                    score += 2
            return score
        
        def find_best_column(metric: str, rules: dict) -> str | None:
            """Encuentra la columna con mayor puntuación, priorizando hints de marca."""
            brand_col_hints = (brand_hints or {}).get(metric, None) if brand_hints else None
            best_col, best_score = None, 0
            for col_lower, col_original in cols_normalized.items():
                s = score_column(col_lower, rules, brand_col_hints)
                if s > best_score:
                    best_score = s
                    best_col = col_original
            return best_col
        
        # Aplicar detección inteligente a cada métrica
        gps_data = {"decel_z5": 0.0, "accel_high": 0.0, "max_speed": 0.0, "distance": 0.0, "sprint_distance": 0.0}
        
        for metric, rules in semantic_rules.items():
            col = find_best_column(metric, rules)
            if col:
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                gps_data[metric] = round(float(vals.mean()), 2) if not vals.empty else 0.0
                print(f"[GPS Adapter] ✓ '{metric}' → '{col}' = {gps_data[metric]}")
            else:
                print(f"[GPS Adapter] ✗ '{metric}' no detectado.")


        # 2. Asociación de Identidad y Temporalidad
        parts = file_path.split("/")
        if len(parts) < 3:
             raise https_fn.HttpsError(https_fn.FunctionsErrorCode.INVALID_ARGUMENT, "Estructura de ruta inválida.")
             
        athlete_id = parts[1]
        date_str = parts[2]
        
        db = firestore.client()
        
        # 3. Cálculo de ACWR (Acute:Chronic Workload Ratio) - Histórico 28 días
        history_ref = db.collection("Daily_Performance") \
            .where("athleteId", "==", athlete_id) \
            .where("date", "<", date_str) \
            .order_by("date", direction=firestore.Query.DESCENDING) \
            .limit(28)
        
        history_docs = history_ref.get()
        loads = [doc.to_dict().get("gps", {}).get("decel_z5", 0) for doc in history_docs]
        
        current_load = gps_data["decel_z5"]
        all_loads = [current_load] + loads
        
        acute_load = sum(all_loads[:7]) / min(len(all_loads), 7) if all_loads else 1.0
        chronic_load = sum(all_loads) / len(all_loads) if all_loads else 1.0
        acwr = round(acute_load / chronic_load, 2) if chronic_load > 0 else 1.0

        # 4. Sincronización Neuro-evaluación (Solo Lectura)
        snap = db.collection("athletes").document(athlete_id).collection("measurements") \
            .where("date", "==", date_str).limit(1).get()
        
        if not snap:
            snap = db.collection("athletes").document(athlete_id).collection("measurements") \
                .order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
        
        imed_snc = {"iri": 75.0, "lapses": 0}
        if snap:
            m = snap[0].to_dict()
            imed_snc["iri"] = float(m.get("iri", 75))
            imed_snc["lapses"] = int(m.get("pvt", {}).get("metrics", {}).get("lapses", 0))

        # 5. Algoritmo IVN (Índice de Vulnerabilidad Neuro-Mecánica)
        iri_norm = max(imed_snc["iri"], 1.0)
        ivn_score = round((acwr * gps_data["decel_z5"]) / (iri_norm / 100), 2)

        # 6. Lógica de Riesgo y Prescripción Técnica
        risk_level = "GREEN"
        ivn_label = "ADAPTACIÓN ÓPTIMA"
        action = "mantener"
        
        if imed_snc["iri"] < 60 and gps_data["decel_z5"] > 15:
            risk_level, ivn_label, action = "RED", "RIESGO CRÍTICO", "optimizar"
        elif imed_snc["lapses"] > 2:
            risk_level, ivn_label, action = "YELLOW", "RIESGO COORDINACIÓN", "reprogramar"
        elif imed_snc["iri"] < 75 or acwr > 1.5:
            risk_level, ivn_label, action = "YELLOW", "RIESGO DE CARGA", "monitorear"

        # 7. Persistencia en Daily_Performance
        doc_id = f"{athlete_id}_{date_str}"
        athlete_snap = db.collection("athletes").document(athlete_id).get()
        athlete_name = athlete_id
        if athlete_snap.exists:
            ad = athlete_snap.to_dict()
            athlete_name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip()

        payload = {
            "athleteId": athlete_id,
            "athleteName": athlete_name,
            "date": date_str,
            "gps": gps_data,
            "acwr": acwr,
            "iri": imed_snc["iri"],
            "lapses": imed_snc["lapses"],
            "ivn_score": ivn_score,
            "risk_level": risk_level,
            "ivn_label": ivn_label,
            "action": action,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "processed_at": firestore.SERVER_TIMESTAMP,
            "metadata": {
                "version": "2.0",
                "formula": "(ACWR * Z5) / (IRI/100)",
                "adapter": "semantic-v2"
            }
        }
        
        db.collection("Daily_Performance").document(doc_id).set(payload, merge=True)
        
        return {
            "status": "success",
            "ivnScore": ivn_score,
            "riskLevel": risk_level,
            "ivnLabel": ivn_label,
            "action": action
        }

    except Exception as e:
        print(f"[ERROR IVN] {str(e)}")
        raise https_fn.HttpsError(https_fn.FunctionsErrorCode.INTERNAL, str(e))
