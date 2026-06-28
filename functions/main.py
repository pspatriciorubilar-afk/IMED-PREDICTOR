from firebase_functions import https_fn, options, firestore_fn, scheduler_fn
from firebase_admin import initialize_app, firestore
import datetime

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
        
        # Reglas semánticas por defecto (motor agnóstico con soporte multi-idioma ES/EN)
        semantic_rules = {
            "decel_z5": {
                "must_any": ["decel", "desacel", "fren", "braking", "frena", "desac", "desac."],
                "boost":    ["high", "alta", "altas", "intense", "z5", "max", "zone 5", "5", "hd", "count", "number", "hi", "(#)"],
                "exclude":  ["distance", "distancia", "power", "band", "low", "baja", "accel", "acel", "ace."]
            },
            "accel_high": {
                "must_any": ["accel", "acel", "acceleration", "acelerac", "ace", "ace."],
                "boost":    ["high", "alta", "altas", "intense", "z5", "max", "ha", "count", "number", "hi", "(#)"],
                "exclude":  ["distance", "distancia", "power", "band", "low", "baja", "decel", "desacel", "desac", "desac."]
            },
            "max_speed": {
                "must_any": ["speed", "velocidad", "velocity", "vel", "vel."],
                "boost":    ["max", "peak", "top", "maximo", "pico", "highest", "maximum"],
                "exclude":  ["average", "avg", "promedio", "band", "zone", "distance", "relative"]
            },
            "distance": {
                "must_any": ["distance", "distancia", "dist", "dist."],
                "boost":    ["total", "covered", "recorrida", "m)", "meters"],
                "exclude":  ["sprint", "high", "band", "zone"]
            },
                "sprint_distance": {
                "must_any": ["sprint", "esprint", "hsr", "alta vel", "high speed", "zona 5", "z5", "distancia sprint", "spr", "spr."],
                "boost":    ["distance", "distancia", "total", "m)"],
                "exclude":  [],
                "agg":      "sum"
            }
        }
        
        # Asignar tipos de agregación por métrica
        metric_agg = {
            "decel_z5": "sum",
            "accel_high": "sum",
            "max_speed": "max",
            "distance": "sum",
            "sprint_distance": "sum"
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
        warnings = []
        
        for metric, rules in semantic_rules.items():
            col = find_best_column(metric, rules)
            if col:
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                if not vals.empty:
                    agg_type = metric_agg.get(metric, "mean")
                    if agg_type == "sum":
                        gps_data[metric] = round(float(vals.sum()), 2)
                    elif agg_type == "max":
                        gps_data[metric] = round(float(vals.max()), 2)
                    else:
                        gps_data[metric] = round(float(vals.mean()), 2)
                    print(f"[GPS Adapter] ✓ '{metric}' ({agg_type}) → '{col}' = {gps_data[metric]}")
                else:
                    gps_data[metric] = 0.0
                    print(f"[GPS Adapter] ⚠ '{metric}' sin datos numéricos en '{col}'")
            else:
                print(f"[GPS Adapter] ✗ '{metric}' no detectado.")
                warnings.append(f"No se detectó '{metric}'")
                
        if warnings:
            gps_data["warnings"] = warnings


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

        # 5. Algoritmo IVN Perfeccionado (Índice de Vulnerabilidad Neuro-Mecánica)
        iri_norm = max(imed_snc["iri"], 1.0)
        iri_factor = iri_norm / 100.0  # Disponibilidad biológica
        
        # Carga Mecánica (60/40)
        decel_raw = gps_data.get("decel_z5", 0.0)
        sprint_raw = gps_data.get("sprint_distance", 0.0)
        sprint_norm = sprint_raw / 10.0  # Normalización
        
        load_decel = 0.6 * decel_raw
        load_sprint = 0.4 * sprint_norm
        carga_mec = load_decel + load_sprint
        
        # IVN = Carga_Mec * (ACWR / IRI)
        ivn_score = round(carga_mec * (acwr / iri_factor), 2)

        # 6. Lógica de Riesgo, Safety Override y Prescripción Táctica
        risk_level = "GREEN"
        ivn_label = "ADAPTACIÓN ÓPTIMA"
        action = "Mantener planificación actual."
        
        # Determinar el driver principal de la carga
        risk_driver = "SPRINT" if load_sprint > load_decel else "DECEL"
        
        # Safety Override (Control Motor)
        if imed_snc["lapses"] > 2:
            risk_level = "RED"
            ivn_label = "CRÍTICO (FALLA SNC)"
            action = "Alerta: Falla de control motor detectada. Riesgo de lesión no traumática (ligamentos). Cese inmediato de carga de alta precisión."
        else:
            # Lógica IVN Normal
            if ivn_score > 30.0 or (iri_norm < 60 and carga_mec > 15):
                risk_level = "RED"
                ivn_label = "RIESGO CRÍTICO"
                if risk_driver == "SPRINT":
                    action = "Alerta: Riesgo de lesión por estiramiento. Limitar esfuerzos lineales de alta velocidad."
                else:
                    action = "Alerta: Riesgo de ruptura excéntrica. Evitar frenados bruscos y cambios de dirección."
            elif ivn_score > 20.0 or acwr > 1.5 or iri_norm < 75:
                risk_level = "YELLOW"
                ivn_label = "ADVERTENCIA"
                if risk_driver == "SPRINT":
                    action = "Precaución: Sobrecarga lineal. Monitorear HSR."
                else:
                    action = "Precaución: Sobrecarga excéntrica. Monitorear aceleraciones/desaceleraciones."

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
            "carga_mec": round(carga_mec, 2),
            "risk_driver": risk_driver,
            "risk_level": risk_level,
            "ivn_label": ivn_label,
            "action": action,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "processed_at": firestore.SERVER_TIMESTAMP,
            "metadata": {
                "version": "3.0",
                "formula": "Carga_Mec * (ACWR / (IRI/100))",
                "adapter": "semantic-v2"
            }
        }
        
        db.collection("Daily_Performance").document(doc_id).set(payload, merge=True)
        
        return {
            "status": "success",
            "ivnScore": ivn_score,
            "riskLevel": risk_level,
            "ivnLabel": ivn_label,
            "action": action,
            "warnings": warnings
        }

    except Exception as e:
        print(f"[ERROR IVN] {str(e)}")
        raise https_fn.HttpsError(https_fn.FunctionsErrorCode.INTERNAL, str(e))

# ── AUTOMATIZACIÓN DE SINCRONIZACIÓN (De aquí en adelante) ───────────────
@firestore_fn.on_document_created(document="athletes/{athlete_id}/measurements/{measurement_id}")
def auto_sync_to_dashboard(event: firestore_fn.Event[firestore_fn.DocumentSnapshot | None]) -> None:
    """
    Sincronizador Automático IMED v3.0
    Asegura que cada test llegue al Dashboard Daily_Performance al instante.
    """
    if event.data is None:
        return

    try:
        athlete_id = event.params["athlete_id"]
        m_data = event.data.to_dict()
        date_str = m_data.get("date")
        
        if not date_str:
            return

        db = firestore.client()
        
        # Obtener nombre del atleta para el panel
        athlete_snap = db.collection("athletes").document(athlete_id).get()
        athlete_name = athlete_id
        if athlete_snap.exists:
            ad = athlete_snap.to_dict()
            athlete_name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip()

        # Datos del PVT
        pvt = m_data.get("pvt", {})
        mean_latency = pvt.get("metrics", {}).get("meanLatency", m_data.get("latency", 0))

        # ── PASO 1: Escribir en Daily_Performance SIEMPRE (sync garantizado) ──
        # Este bloque se ejecuta de forma independiente al análisis Ex-Gaussiano.
        # Un fallo del worker NO debe impedir que el dato llegue al Dashboard.
        doc_id = f"{athlete_id}_{date_str}"
        payload = {
            "athleteId": athlete_id,
            "athleteName": athlete_name,
            "date": date_str,
            "iri": m_data.get("iri"),
            "status": m_data.get("status"),
            "lapses": pvt.get("metrics", {}).get("lapses", 0),
            "latency": mean_latency,
            "wellness": m_data.get("wellness"),
            "pvt": m_data.get("pvt"),
            "timestamp": firestore.SERVER_TIMESTAMP,
            "sync_method": "auto_trigger_v411"
        }
        
        # Guardar en Daily_Performance (merge=True para no borrar datos GPS si ya existen)
        db.collection("Daily_Performance").document(doc_id).set(payload, merge=True)
        print(f"[AUTO-SYNC] ✅ Daily_Performance actualizado para {athlete_name} ({date_str})")

        # ── PASO 2: DISPARADOR EX-GAUSSIANO (best-effort, no bloquea el sync) ──
        # Encapsulado en try/except independiente: si falla, el dato ya está guardado.
        try:
            import pvt_exgauss_worker
            
            pvt_data = m_data.get("pvt", {})
            metrics_data = pvt_data.get("metrics", {})
            # Buscar trials en todos los paths posibles (compatibilidad multi-versión)
            trials = (
                metrics_data.get("trials") or
                metrics_data.get("rawReactionTimes") or
                pvt_data.get("trials") or
                pvt_data.get("logs") or
                m_data.get("trials") or
                []
            )
            
            if trials:
                measurement_payload = {
                    "athlete_id": athlete_id,
                    "athlete_name": athlete_name,
                    "date": date_str,
                    "trials": [float(t) for t in trials if isinstance(t, (int, float))],
                    "wellness": m_data.get("wellness"),
                    "iri": m_data.get("iri")
                }
                print(f"[AUTO-SYNC] Disparando análisis Ex-Gaussiano para {athlete_name}...")
                pvt_exgauss_worker.process_athlete(db, measurement_payload, date_str)
                print(f"[AUTO-SYNC] ✅ Análisis Ex-Gaussiano completado.")
            else:
                print(f"[AUTO-SYNC] Sin trials crudos PVT para {athlete_name}. Se omite Ex-Gauss.")
                
        except Exception as ex_err:
            # IMPORTANTE: Este error NO cancela el sync. El dato ya fue guardado arriba.
            print(f"[ERROR EX-GAUSS RT] ⚠️ Worker falló (dato sincronizado de todas formas): {str(ex_err)}")

    except Exception as e:
        print(f"[ERROR AUTO-SYNC] {str(e)}")

@https_fn.on_call()
def force_sync_athlete(req: https_fn.CallableRequest) -> dict:
    """Función para recuperación manual de datos perdidos."""
    athlete_id = req.data.get("athleteId")
    date_str = req.data.get("date")
    
    if not athlete_id or not date_str:
        raise https_fn.HttpsError(https_fn.FunctionsErrorCode.INVALID_ARGUMENT, "Faltan parámetros.")
        
    db = firestore.client()
    measurements = db.collection("athletes").document(athlete_id).collection("measurements") \
        .where("date", "==", date_str).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
        
    if not measurements:
        return {"status": "error", "message": "No se hallaron mediciones para esa fecha."}
        
    m_data = measurements[0].to_dict()
    athlete_snap = db.collection("athletes").document(athlete_id).get()
    athlete_name = f"{athlete_snap.to_dict().get('firstName','')} {athlete_snap.to_dict().get('lastName','')}".strip() if athlete_snap.exists else athlete_id

    pvt = m_data.get("pvt", {})
    mean_latency = pvt.get("metrics", {}).get("meanLatency", m_data.get("latency", 0))

    payload = {
        "athleteId": athlete_id,
        "athleteName": athlete_name,
        "date": date_str,
        "iri": m_data.get("iri"),
        "status": m_data.get("status"),
        "lapses": pvt.get("metrics", {}).get("lapses", 0),
        "latency": mean_latency,
        "wellness": m_data.get("wellness"),
        "pvt": pvt,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "sync_method": "forced_recovery"
    }
    
    db.collection("Daily_Performance").document(f"{athlete_id}_{date_str}").set(payload, merge=True)
    return {"status": "success", "message": f"Datos de {athlete_name} sincronizados."}

@https_fn.on_call()
def sync_athlete_history(req: https_fn.CallableRequest) -> dict:
    """
    Fuerza la sincronización completa del historial de un atleta desde 'measurements' a 'Daily_Performance'.
    Resuelve problemas de datos truncados o faltantes en el Dashboard.
    """
    athlete_id = req.data.get("athleteId")
    if not athlete_id:
        return {"error": "athleteId requerido"}
        
    db = firestore.client()
    try:
        m_docs = db.collection("athletes").document(athlete_id).collection("measurements").get()
        synced = 0
        for doc in m_docs:
            m = doc.to_dict()
            raw_ts = m.get("timestamp", "")
            date = m.get("date") or (raw_ts[:10] if isinstance(raw_ts, str) else "")
            if not date: continue
            
            pvt = m.get("pvt", {})
            mean_lat = pvt.get("metrics", {}).get("meanLatency", m.get("latency", 0))

            # Obtener nombre del atleta para el dashboard (sin esta línea se muestra undefined)
            ath_snap = db.collection("athletes").document(athlete_id).get()
            ath_name = athlete_id
            if ath_snap.exists:
                ad = ath_snap.to_dict()
                ath_name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip() or athlete_id

            db.collection("Daily_Performance").document(f"{athlete_id}_{date}").set({
                "athleteId":   athlete_id,
                "athleteName": ath_name,
                "date":        date,
                "iri":         m.get("iri", 0),
                "pvt":         pvt,
                "latency":     mean_lat,
                "wellness":    m.get("wellness", {}),
                "sync_method": "manual_sync_repair_v4"
            }, merge=True)
            synced += 1
            
        return {"success": True, "synced_records": synced}
    except Exception as e:
        return {"success": False, "error": str(e)}


@https_fn.on_call()
def manual_register(req: https_fn.CallableRequest) -> dict:
    """
    Registro manual de evaluación desde el Dashboard.
    Permite ingresar los resultados de un atleta directamente sin necesitar la app móvil.
    Útil cuando el dato quedó guardado localmente en el dispositivo y no sincronizó.
    
    Parámetros esperados:
        athleteId   : ID del atleta en Firestore
        date        : Fecha en formato YYYY-MM-DD
        iri         : Índice de Recuperación Integrado (0-100)
        lapses      : Número de lapsos de atención en PVT
        meanLatency : Latencia media de reacción en ms (opcional)
        sleepHours  : Horas de sueño (opcional, wellness)
        sleepQuality: Calidad del sueño 1-5 (opcional, wellness)
        stressLevel : Nivel de estrés 1-5 (opcional, wellness)
        fatigueLevel: Nivel de fatiga 1-5 (opcional, wellness)
    """
    db = firestore.client()
    try:
        athlete_id   = req.data.get("athleteId", "").strip()
        date_str     = req.data.get("date", "").strip()
        iri          = int(req.data.get("iri", 0))
        lapses       = int(req.data.get("lapses", 0))
        mean_latency = int(req.data.get("meanLatency", 0))

        if not athlete_id or not date_str:
            return {"status": "error", "message": "athleteId y date son requeridos."}

        # Calcular estado SNC en base al IRI
        if iri >= 85:
            status = "OPTIMO"
        elif iri >= 70:
            status = "ESTABLE"
        elif iri >= 60:
            status = "ADVERTENCIA"
        else:
            status = "CRITICO"

        # Obtener nombre del atleta
        athlete_doc = db.collection("athletes").document(athlete_id).get()
        if athlete_doc.exists:
            ad = athlete_doc.to_dict()
            athlete_name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip() or athlete_id
        else:
            athlete_name = athlete_id

        # Wellness (opcional)
        wellness = {
            "sleepHours":    req.data.get("sleepHours"),
            "sleepQuality":  req.data.get("sleepQuality"),
            "stressLevel":   req.data.get("stressLevel"),
            "fatigueLevel":  req.data.get("fatigueLevel"),
        }

        # Escribir en athletes/{id}/measurements para mantener historial
        meas_payload = {
            "date":      date_str,
            "timestamp": date_str + "T12:00:00",
            "iri":       iri,
            "status":    status,
            "wellness":  wellness,
            "pvt": {
                "metrics": {
                    "meanLatency": mean_latency,
                    "lapses":      lapses,
                }
            },
            "sync_method": "manual_dashboard_entry",
            "syncedAt":    firestore.SERVER_TIMESTAMP,
        }
        db.collection("athletes").document(athlete_id)\
          .collection("measurements").add(meas_payload)

        # Escribir en Daily_Performance (lo que ve el dashboard)
        doc_id = f"{athlete_id}_{date_str}"
        dp_payload = {
            "athleteId":   athlete_id,
            "athleteName": athlete_name,
            "date":        date_str,
            "iri":         iri,
            "status":      status,
            "lapses":      lapses,
            "latency":     mean_latency,
            "wellness":    wellness,
            "pvt": {
                "metrics": {
                    "meanLatency": mean_latency,
                    "lapses":      lapses,
                }
            },
            "timestamp":   firestore.SERVER_TIMESTAMP,
            "sync_method": "manual_dashboard_entry",
        }
        db.collection("Daily_Performance").document(doc_id).set(dp_payload, merge=True)

        print(f"[MANUAL] Registro manual creado: {athlete_name} ({date_str}) | IRI: {iri} | Status: {status}")
        return {
            "status":  "success",
            "message": f"Evaluacion de {athlete_name} registrada correctamente para {date_str}.",
            "iri":     iri,
            "sncStatus": status,
        }

    except Exception as e:
        print(f"[MANUAL-ERROR] {str(e)}")
        return {"status": "error", "message": str(e)}


# ==============================================================================
# USER MANAGEMENT (RBAC)
# ==============================================================================

@https_fn.on_call()
def list_dashboard_users(req: https_fn.CallableRequest) -> dict:
    """Lista todos los usuarios de Firebase Auth para el panel de administración."""
    from firebase_admin import auth
    
    # Solo ADMIN puede listar
    # En un entorno estricto verificaríamos el token, pero para la demo inicial validamos desde cliente.
    # user_role = req.auth.token.get('role') si req.auth else None
    
    try:
        users = []
        page = auth.list_users()
        while page:
            for user in page.users:
                role = user.custom_claims.get('role', 'COACH') if user.custom_claims else 'COACH'
                team = user.custom_claims.get('team', '') if user.custom_claims else ''
                # Identificar si es la cuenta DEMO
                if user.email == 'demo@imedpredictor.com':
                    role = 'DEMO'
                    
                users.append({
                    "uid": user.uid,
                    "email": user.email,
                    "role": role,
                    "team": team,
                    "creationTime": user.user_metadata.creation_timestamp
                })
            page = page.get_next_page()
            
        return {"status": "success", "users": users}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@https_fn.on_call()
def create_dashboard_user(req: https_fn.CallableRequest) -> dict:
    """Crea un usuario en Firebase Auth y le asigna un rol."""
    from firebase_admin import auth
    
    email = req.data.get("email")
    password = req.data.get("password")
    role = req.data.get("role", "COACH")
    team = req.data.get("team", "")
    
    if not email or not password:
        return {"status": "error", "message": "Email y contraseña requeridos."}
        
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        claims = {'role': role}
        if team:
            claims['team'] = team
            
        auth.set_custom_user_claims(user.uid, claims)
        return {"status": "success", "message": f"Usuario {email} creado con rol {role}."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@https_fn.on_call()
def delete_dashboard_user(req: https_fn.CallableRequest) -> dict:
    """Elimina un usuario de Firebase Auth."""
    from firebase_admin import auth
    uid = req.data.get("uid")
    
    if not uid:
        return {"status": "error", "message": "UID requerido."}
        
    try:
        # Prevenir borrar la cuenta demo si está hardcodeada
        user = auth.get_user(uid)
        if user.email == 'demo@imedpredictor.com':
            return {"status": "error", "message": "No se puede eliminar la cuenta DEMO oficial."}
            
        auth.delete_user(uid)
        return {"status": "success", "message": "Usuario eliminado."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@https_fn.on_call()
def update_dashboard_user_team(req: https_fn.CallableRequest) -> dict:
    """Actualiza la plantilla (team) asignada a un usuario."""
    from firebase_admin import auth
    uid = req.data.get("uid")
    team = req.data.get("team", "")
    
    if not uid:
        return {"status": "error", "message": "UID requerido."}
        
    try:
        user = auth.get_user(uid)
        claims = user.custom_claims or {}
        
        if team:
            claims['team'] = team
        else:
            claims.pop('team', None)
            
        auth.set_custom_user_claims(uid, claims)
        return {"status": "success", "message": "Plantilla actualizada con éxito."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
