from firebase_functions import https_fn, options, firestore_fn, scheduler_fn
from firebase_admin import initialize_app, firestore
import datetime

# Configuración global - Rendimiento Optimizado (Plan Blaze)
options.set_global_options(region="us-central1", timeout_sec=60, memory=512)
initialize_app()

# ==============================================================================
# RBAC — ROLES Y HELPERS DE AUTORIZACIÓN (Sprint 1)
# ==============================================================================

# Jerarquía de roles (orden ascendente de privilegios)
ROLE_DEPORTISTA  = "DEPORTISTA"
ROLE_PSICOLOGO   = "PSICOLOGO"
ROLE_COACH       = "COACH"
ROLE_SUPER_ADMIN = "SUPER_ADMIN"

# Conjuntos de roles para cada nivel de acceso
ROLES_DASHBOARD  = {ROLE_COACH, ROLE_PSICOLOGO, ROLE_SUPER_ADMIN}
ROLES_CLINICAL   = {ROLE_PSICOLOGO, ROLE_SUPER_ADMIN}
ROLES_ADMIN_ONLY = {ROLE_SUPER_ADMIN}


def _get_caller_role(req: https_fn.CallableRequest) -> str | None:
    """
    Extrae el rol del Custom Claim del token JWT del llamador.
    Retorna None si el usuario no está autenticado o no tiene claim de rol.
    """
    if req.auth is None:
        return None
    return req.auth.token.get("role", None)


def _require_role(req: https_fn.CallableRequest, allowed_roles: set) -> None:
    """
    Verifica que el llamador tenga uno de los roles permitidos.
    Lanza HttpsError(PERMISSION_DENIED) si no cumple.

    Args:
        req:           La request del callable de Cloud Functions.
        allowed_roles: Conjunto de roles que pueden ejecutar el endpoint.

    Raises:
        https_fn.HttpsError: Con código PERMISSION_DENIED si el rol no está autorizado.
                             Con código UNAUTHENTICATED si no hay sesión activa.
    """
    if req.auth is None:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            "Acceso denegado: se requiere autenticación."
        )

    role = _get_caller_role(req)

    # Verificar si la cuenta está bloqueada por suscripción vencida
    blocked = req.auth.token.get("blocked", False)
    if blocked:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            "Cuenta bloqueada: la suscripción ha expirado. Contacta al administrador."
        )

    if role not in allowed_roles:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            f"Acceso denegado: se requiere rol {allowed_roles}. Rol actual: '{role}'."
        )


def _log_audit(action: str, actor_uid: str, target: str, details: dict = None) -> None:
    """
    Escribe un registro inmutable en la colección audit_log via Admin SDK.
    El Admin SDK bypasea las Firestore Security Rules — solo Cloud Functions puede escribir aquí.

    Args:
        action:    Nombre de la acción (ej. "CREATE_USER", "DELETE_USER", "CHECK_SUBSCRIPTION").
        actor_uid: UID del usuario que ejecutó la acción.
        target:    Recurso afectado (ej. email del usuario creado, UID del deportista).
        details:   Datos adicionales opcionales (no incluir datos sensibles/clínicos).
    """
    try:
        db = firestore.client()
        db.collection("audit_log").add({
            "action":     action,
            "actor_uid":  actor_uid,
            "target":     target,
            "details":    details or {},
            "timestamp":  firestore.SERVER_TIMESTAMP,
        })
    except Exception as e:
        # El audit log nunca debe romper el flujo principal — solo se registra el error
        import logging
        logging.getLogger("IMED-RBAC").error(f"[AUDIT-LOG-ERROR] No se pudo escribir log: {e}")

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
def _execute_exgauss_analysis(db, athlete_id: str, athlete_name: str, date_str: str, m_data: dict) -> None:
    """
    Ejecuta el worker Ex-Gaussiano en cualquier proceso de sync o recuperación.
    Asegura que los cálculos Tau/Z-Score nunca falten al regenerar Daily_Performance.

    FIX: Si m_data no contiene trials (race condition del trigger Firestore),
    se realiza un fallback leyendo la medición directamente desde Firestore.
    Esto garantiza que el análisis siempre se ejecute cuando hay ≥20 trials.
    """
    try:
        import pvt_exgauss_worker
        pvt_data = m_data.get("pvt", {})
        metrics_data = pvt_data.get("metrics", {})
        trials = (
            metrics_data.get("trials") or
            metrics_data.get("rawReactionTimes") or
            pvt_data.get("trials") or
            pvt_data.get("logs") or
            m_data.get("trials") or
            []
        )

        # ── FALLBACK: Si no hay trials en m_data, leer directamente desde Firestore ──
        # Esto resuelve el race condition donde el trigger se dispara antes de que
        # la app mobile termine de escribir todos los campos del documento.
        if not trials:
            print(f"[EX-GAUSS] Sin trials en m_data para {athlete_name} ({date_str}). Leyendo desde Firestore...")
            fresh_docs = (
                db.collection("athletes").document(athlete_id)
                .collection("measurements")
                .where("date", "==", date_str)
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(1)
                .stream()
            )
            for fresh_doc in fresh_docs:
                fresh = fresh_doc.to_dict()
                pvt_fresh = fresh.get("pvt", {})
                metrics_fresh = pvt_fresh.get("metrics", {})
                trials = (
                    metrics_fresh.get("trials") or
                    metrics_fresh.get("rawReactionTimes") or
                    pvt_fresh.get("trials") or
                    pvt_fresh.get("logs") or
                    fresh.get("trials") or
                    []
                )
                # Actualizar m_data con los datos frescos del wellness
                if not m_data.get("wellness") and fresh.get("wellness"):
                    m_data = fresh
                if trials:
                    print(f"[EX-GAUSS] Fallback exitoso: {len(trials)} trials encontrados en Firestore para {athlete_name} ({date_str}).")
                break

        if not trials:
            print(f"[EX-GAUSS] Sin trials disponibles para {athlete_name} ({date_str}). Saltando análisis.")
            return

        valid_trials = [float(t) for t in trials if isinstance(t, (int, float))]
        if not valid_trials:
            print(f"[EX-GAUSS] Trials no son numéricos para {athlete_name} ({date_str}). Saltando análisis.")
            return

        measurement_payload = {
            "athlete_id": athlete_id,
            "athlete_name": athlete_name,
            "date": date_str,
            "trials": valid_trials,
            "wellness": m_data.get("wellness"),
            "iri": m_data.get("iri")
        }
        pvt_exgauss_worker.process_athlete(db, measurement_payload, date_str)
        print(f"[EX-GAUSS] ✅ Análisis completado para {athlete_name} ({date_str}).")
    except Exception as ex_err:
        import traceback
        print(f"[ERROR EX-GAUSS] Worker falló en {athlete_name} ({date_str}): {str(ex_err)}")
        traceback.print_exc()

@firestore_fn.on_document_created(document="athletes/{athlete_id}/measurements/{measurement_id}")
def auto_sync_to_dashboard(event: firestore_fn.Event[firestore_fn.DocumentSnapshot | None]) -> None:
    """
    Sincronizador Automático IMED v3.0
    Asegura que cada test llegue al Dashboard Daily_Performance al instante.
    """
    if event.data is None:
        return

    try:
        import urllib.parse
        athlete_id = urllib.parse.unquote(event.params["athlete_id"])
        m_data = event.data.to_dict()
        date_str = m_data.get("date")
        
        if not date_str:
            return

        db = firestore.client()
        
        # Obtener nombre y tenantId del atleta para el panel
        athlete_snap = db.collection("athletes").document(athlete_id).get()
        athlete_name = athlete_id
        tenant_id = None
        if athlete_snap.exists:
            ad = athlete_snap.to_dict()
            athlete_name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip()
            tenant_id = ad.get("tenantId")

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
        if tenant_id:
            payload["tenantId"] = tenant_id
        
        # Guardar en Daily_Performance (merge=True para no borrar datos GPS si ya existen)
        db.collection("Daily_Performance").document(doc_id).set(payload, merge=True)
        print(f"[AUTO-SYNC] ✅ Daily_Performance actualizado para {athlete_name} ({date_str})")

        # ── PASO 2: DISPARADOR EX-GAUSSIANO (best-effort, no bloquea el sync) ──
        # NOTA: Se pasa m_data con la data del evento. Si el evento no tiene trials
        # (race condition), _execute_exgauss_analysis hace fallback a Firestore.
        _execute_exgauss_analysis(db, athlete_id, athlete_name, date_str, m_data)

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
    _execute_exgauss_analysis(db, athlete_id, athlete_name, date_str, m_data)
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
            _execute_exgauss_analysis(db, athlete_id, ath_name, date, m)
            synced += 1
            
        return {"success": True, "synced_records": synced}
    except Exception as e:
        return {"success": False, "error": str(e)}


@https_fn.on_call()
def deduplicate_athlete_measurements(req: https_fn.CallableRequest) -> dict:
    """
    Limpieza de registros duplicados para un atleta.
    Problema: versiones anteriores escribían 2 documentos en measurements/ por sesión,
    lo que disparaba el trigger auto_sync_to_dashboard dos veces, generando duplicados
    en Daily_Performance.

    Estrategia de deduplicación:
    - Agrupa todos los measurements por fecha (YYYY-MM-DD).
    - Por cada fecha, conserva SOLO el documento con mayor IRI (el más completo).
    - Elimina el resto de duplicados.
    - Luego regenera Daily_Performance desde los measurements limpios.

    Parámetros:
        athleteId : ID del atleta (ej. el ID de Diego Dañobeytia en Firestore)
        dryRun    : Si true, solo reporta sin eliminar (default: false)
    """
    athlete_id = req.data.get("athleteId", "").strip()
    dry_run    = req.data.get("dryRun", False)

    if not athlete_id:
        return {"status": "error", "message": "athleteId requerido."}

    db = firestore.client()

    try:
        # 1. Obtener nombre del atleta
        athlete_snap = db.collection("athletes").document(athlete_id).get()
        athlete_name = athlete_id
        if athlete_snap.exists:
            ad = athlete_snap.to_dict()
            athlete_name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip() or athlete_id

        # 2. Cargar todos los measurements del atleta
        m_docs = db.collection("athletes").document(athlete_id)\
                   .collection("measurements").get()

        # 3. Agrupar por fecha → {date_str: [lista de (doc_id, iri, doc_ref)]}
        by_date: dict[str, list] = {}
        for doc in m_docs:
            data = doc.to_dict()
            # Extraer fecha — soporta campo 'date' o parsear 'timestamp'
            raw_ts = data.get("timestamp", "")
            date_str = data.get("date")
            if not date_str:
                if isinstance(raw_ts, str) and len(raw_ts) >= 10:
                    date_str = raw_ts[:10]
                else:
                    continue  # Sin fecha → ignorar

            iri = data.get("iri", 0) or 0
            if date_str not in by_date:
                by_date[date_str] = []
            by_date[date_str].append({
                "id":   doc.id,
                "ref":  doc.reference,
                "iri":  iri,
                "data": data,
            })

        # 4. Por cada fecha, elegir el MEJOR documento (mayor IRI) y marcar el resto para borrado
        to_delete = []
        report    = []

        for date_str, docs in by_date.items():
            if len(docs) <= 1:
                continue  # Sin duplicados en esta fecha

            # Ordenar por IRI descendente → el primero es el mejor
            docs_sorted = sorted(docs, key=lambda d: d["iri"], reverse=True)
            best   = docs_sorted[0]
            extras = docs_sorted[1:]

            report.append({
                "date":       date_str,
                "duplicates": len(extras),
                "kept_id":    best["id"],
                "kept_iri":   best["iri"],
                "deleted_ids": [d["id"] for d in extras],
            })

            for dup in extras:
                to_delete.append(dup["ref"])

        # 5. Eliminar duplicados (si no es dry_run)
        deleted_count = 0
        if not dry_run:
            for ref in to_delete:
                ref.delete()
                deleted_count += 1

            # 6. Regenerar Daily_Performance desde el historial limpio
            #    Volver a cargar para asegurar que usamos los docs correctos
            clean_docs = db.collection("athletes").document(athlete_id)\
                           .collection("measurements").get()

            for doc in clean_docs:
                data = doc.to_dict()
                raw_ts   = data.get("timestamp", "")
                date_str = data.get("date") or (raw_ts[:10] if isinstance(raw_ts, str) else None)
                if not date_str:
                    continue

                pvt      = data.get("pvt", {})
                mean_lat = pvt.get("metrics", {}).get("meanLatency", data.get("latency", 0))
                iri      = data.get("iri", 0) or 0
                lapses   = pvt.get("metrics", {}).get("lapses", 0)

                db.collection("Daily_Performance").document(f"{athlete_id}_{date_str}").set({
                    "athleteId":   athlete_id,
                    "athleteName": athlete_name,
                    "date":        date_str,
                    "iri":         iri,
                    "status":      data.get("status", ""),
                    "lapses":      lapses,
                    "latency":     mean_lat,
                    "wellness":    data.get("wellness"),
                    "pvt":         pvt,
                    "timestamp":   firestore.SERVER_TIMESTAMP,
                    "sync_method": "dedup_repair_v1",
                }, merge=True)
                _execute_exgauss_analysis(db, athlete_id, athlete_name, date_str, data)

        print(f"[DEDUP] ✅ {athlete_name}: {deleted_count} duplicados eliminados | fechas afectadas: {len(report)}")
        return {
            "status":         "success",
            "athleteName":    athlete_name,
            "dry_run":        dry_run,
            "deleted":        deleted_count,
            "dates_affected": len(report),
            "report":         report,
        }

    except Exception as e:
        print(f"[DEDUP-ERROR] {str(e)}")
        return {"status": "error", "message": str(e)}


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
        athlete_id      = req.data.get("athleteId", "").strip()
        date_str        = req.data.get("date", "").strip()
        iri             = int(req.data.get("iri", 0))
        lapses          = int(req.data.get("lapses", 0))
        mean_latency    = int(req.data.get("meanLatency", 0))
        # Protocolo Híbrido v2.1: contexto de línea base estática
        # Valores válidos: "PRE_SEASON" | "IN_SEASON" | "COMPETITION_WEEK" | "UNKNOWN"
        baseline_context = req.data.get("baselineContext", "UNKNOWN").strip()
        VALID_BASELINE_CONTEXTS = {"PRE_SEASON", "IN_SEASON", "COMPETITION_WEEK", "UNKNOWN"}
        if baseline_context not in VALID_BASELINE_CONTEXTS:
            baseline_context = "UNKNOWN"

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
            # Persistir baseline_context si aún no estaba definido (primera vez)
            if not ad.get("baseline_context") or ad.get("baseline_context") == "UNKNOWN":
                db.collection("athletes").document(athlete_id).update({
                    "baseline_context":    baseline_context,
                    "baseline_start_date": date_str,
                })
                print(f"[MANUAL] baseline_context seteado: {athlete_name} → {baseline_context} (desde {date_str})")
        else:
            athlete_name = athlete_id

        # Wellness (opcional)
        wellness = {
            "sleepHours":    req.data.get("sleepHours"),
            "sleepQuality":  req.data.get("sleepQuality"),
            "stressLevel":   req.data.get("stressLevel"),
            "fatigueLevel":  req.data.get("fatigueLevel"),
        }

        # Escribir en athletes/{id}/measurements para mantener historial.
        # IMPORTANTE: El trigger 'auto_sync_to_dashboard' detectará esta escritura
        # y propagará automáticamente los datos a Daily_Performance.
        # NO se escribe directamente en Daily_Performance aquí para evitar el
        # doble registro (trigger + escritura directa = 2 documentos idénticos).
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


@https_fn.on_call()
def set_athlete_baseline_context(req: https_fn.CallableRequest) -> dict:
    """
    Protocolo Híbrido v2.1 — Actualiza el contexto de la Línea Base Estática de un atleta.
    Permite al psicólogo indicar en qué contexto se capturaron las primeras mediciones
    (onboarding), para que el sistema etiquete correctamente la calidad del baseline.

    Este campo es almacenado en athletes/{id} y en cada registro de Daily_Performance
    a través del worker Ex-Gaussiano. Su impacto es de trazabilidad clínica — no altera
    el cálculo matemático, pero queda registrado como advertencia interpretativa.

    Parámetros:
        athleteId:       ID del atleta en Firestore
        baselineContext: "PRE_SEASON" | "IN_SEASON" | "COMPETITION_WEEK" | "UNKNOWN"
        baselineStartDate: (opcional) Fecha de inicio de la línea base (YYYY-MM-DD)
    """
    caller_role = _get_caller_role(req)
    if caller_role not in {ROLE_PSICOLOGO, ROLE_SUPER_ADMIN}:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            "Acceso denegado: se requiere rol de Psicólogo o Super Admin."
        )

    athlete_id   = req.data.get("athleteId", "").strip()
    context      = req.data.get("baselineContext", "UNKNOWN").strip()
    start_date   = req.data.get("baselineStartDate", "").strip()

    VALID_CONTEXTS = {"PRE_SEASON", "IN_SEASON", "COMPETITION_WEEK", "UNKNOWN"}
    if not athlete_id:
        return {"status": "error", "message": "athleteId requerido."}
    if context not in VALID_CONTEXTS:
        return {"status": "error", "message": f"Contexto inválido. Valores permitidos: {VALID_CONTEXTS}"}

    db = firestore.client()
    try:
        athlete_snap = db.collection("athletes").document(athlete_id).get()
        if not athlete_snap.exists:
            return {"status": "error", "message": "Atleta no encontrado."}

        ad = athlete_snap.to_dict()
        athlete_name = f"{ad.get('firstName','')} {ad.get('lastName','')}".strip() or athlete_id

        update_data = {"baseline_context": context}
        if start_date:
            update_data["baseline_start_date"] = start_date

        db.collection("athletes").document(athlete_id).update(update_data)

        _log_audit(
            action="SET_BASELINE_CONTEXT",
            actor_uid=req.auth.uid,
            target=athlete_id,
            details={
                "athlete_name":    athlete_name,
                "baseline_context": context,
                "baseline_start_date": start_date or "(no especificada)",
            }
        )
        print(f"[BASELINE-CTX] {athlete_name}: baseline_context='{context}' | start='{start_date}'")
        return {
            "status":  "success",
            "message": f"Contexto de línea base de {athlete_name} actualizado a '{context}'.",
            "athlete_name":     athlete_name,
            "baseline_context": context,
        }
    except Exception as e:
        print(f"[BASELINE-CTX-ERROR] {str(e)}")
        return {"status": "error", "message": str(e)}


# ==============================================================================
# USER MANAGEMENT (RBAC)
# ==============================================================================

@https_fn.on_call()
def list_dashboard_users(req: https_fn.CallableRequest) -> dict:
    """Lista todos los usuarios del inquilino del llamador (o todos si es SUPER_ADMIN)."""
    from firebase_admin import auth

    caller_role = _get_caller_role(req)
    if caller_role != ROLE_SUPER_ADMIN and caller_role != ROLE_PSICOLOGO:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            "Acceso denegado: se requiere rol de Administrador o Psicólogo."
        )

    caller_tenant_id = req.auth.token.get("tenantId") if req.auth else None
    if caller_role == ROLE_PSICOLOGO and not caller_tenant_id:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            "Acceso denegado: cuenta de psicólogo sin inquilino asociado."
        )

    try:
        users = []
        page = auth.list_users()
        while page:
            for user in page.users:
                claims = user.custom_claims or {}
                role = claims.get('role', 'COACH')
                team = claims.get('team', '')
                blocked = claims.get('blocked', False)
                tenant_id = claims.get('tenantId', '')

                # Identificar si es la cuenta DEMO
                if user.email == 'demo@imedpredictor.com':
                    role = 'DEMO'

                # Filtrar por tenantId si el llamador no es SUPER_ADMIN
                if caller_role != ROLE_SUPER_ADMIN:
                    if tenant_id != caller_tenant_id:
                        continue  # Omitir usuarios de otros tenants

                users.append({
                    "uid":          user.uid,
                    "email":        user.email,
                    "role":         role,
                    "team":         team,
                    "blocked":      blocked,
                    "tenantId":     tenant_id,
                    "creationTime": user.user_metadata.creation_timestamp
                })
            page = page.get_next_page()

        _log_audit("LIST_USERS", req.auth.uid, f"{len(users)} usuarios listados")
        return {"status": "success", "users": users}
    except https_fn.HttpsError:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


@https_fn.on_call()
def create_dashboard_user(req: https_fn.CallableRequest) -> dict:
    """Crea un usuario en Firebase Auth y le asigna un rol y tenantId."""
    from firebase_admin import auth

    caller_role = _get_caller_role(req)
    if caller_role != ROLE_SUPER_ADMIN and caller_role != ROLE_PSICOLOGO:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            "Acceso denegado: se requiere rol de Administrador o Psicólogo."
        )

    caller_tenant_id = req.auth.token.get("tenantId") if req.auth else None
    if caller_role == ROLE_PSICOLOGO and not caller_tenant_id:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            "Acceso denegado: cuenta de psicólogo sin inquilino asociado."
        )

    email    = req.data.get("email", "").strip()
    password = req.data.get("password", "")
    role     = req.data.get("role", ROLE_COACH)
    team     = req.data.get("team", "")

    # Validar que el rol solicitado sea uno de los roles válidos del sistema
    valid_roles = {ROLE_DEPORTISTA, ROLE_COACH, ROLE_PSICOLOGO}
    if role not in valid_roles:
        return {"status": "error", "message": f"Rol inválido: '{role}'."}

    if not email or not password:
        return {"status": "error", "message": "Email y contraseña requeridos."}

    try:
        user = auth.create_user(email=email, password=password)
        claims = {"role": role}
        if team:
            claims["team"] = team

        # Asignar tenantId
        if caller_role == ROLE_SUPER_ADMIN:
            requested_tenant = req.data.get("tenantId", "").strip()
            if requested_tenant:
                claims["tenantId"] = requested_tenant
        else:
            claims["tenantId"] = caller_tenant_id

        auth.set_custom_user_claims(user.uid, claims)

        _log_audit(
            action="CREATE_USER",
            actor_uid=req.auth.uid,
            target=email,
            details={"role": role, "team": team, "new_uid": user.uid, "tenantId": claims.get("tenantId")}
        )
        return {"status": "success", "message": f"Usuario {email} creado con rol {role}."}
    except https_fn.HttpsError:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


@https_fn.on_call()
def delete_dashboard_user(req: https_fn.CallableRequest) -> dict:
    """Elimina un usuario de Firebase Auth. Requiere SUPER_ADMIN o Psicólogo dueño del tenant."""
    from firebase_admin import auth

    caller_role = _get_caller_role(req)
    if caller_role != ROLE_SUPER_ADMIN and caller_role != ROLE_PSICOLOGO:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            "Acceso denegado: se requiere rol de Administrador o Psicólogo."
        )

    caller_tenant_id = req.auth.token.get("tenantId") if req.auth else None
    if caller_role == ROLE_PSICOLOGO and not caller_tenant_id:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            "Acceso denegado: cuenta de psicólogo sin inquilino asociado."
        )

    uid = req.data.get("uid", "").strip()
    if not uid:
        return {"status": "error", "message": "UID requerido."}

    try:
        user = auth.get_user(uid)

        # Si el llamador es Psicólogo, validar que el usuario pertenece a su tenant
        if caller_role == ROLE_PSICOLOGO:
            user_claims = user.custom_claims or {}
            if user_claims.get("tenantId") != caller_tenant_id:
                raise https_fn.HttpsError(
                    https_fn.FunctionsErrorCode.PERMISSION_DENIED,
                    "Acceso denegado: el usuario no pertenece a tu organización."
                )

        if user.email == 'demo@imedpredictor.com':
            return {"status": "error", "message": "No se puede eliminar la cuenta DEMO oficial."}

        auth.delete_user(uid)

        _log_audit(
            action="DELETE_USER",
            actor_uid=req.auth.uid,
            target=uid,
            details={"deleted_email": user.email}
        )
        return {"status": "success", "message": "Usuario eliminado."}
    except https_fn.HttpsError:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


@https_fn.on_call()
def update_dashboard_user_team(req: https_fn.CallableRequest) -> dict:
    """Actualiza la plantilla (team) asignada a un usuario. Requiere SUPER_ADMIN o Psicólogo dueño del tenant."""
    from firebase_admin import auth

    caller_role = _get_caller_role(req)
    if caller_role != ROLE_SUPER_ADMIN and caller_role != ROLE_PSICOLOGO:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            "Acceso denegado: se requiere rol de Administrador o Psicólogo."
        )

    caller_tenant_id = req.auth.token.get("tenantId") if req.auth else None
    if caller_role == ROLE_PSICOLOGO and not caller_tenant_id:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            "Acceso denegado: cuenta de psicólogo sin inquilino asociado."
        )

    uid  = req.data.get("uid", "").strip()
    team = req.data.get("team", "")

    if not uid:
        return {"status": "error", "message": "UID requerido."}

    try:
        user   = auth.get_user(uid)
        claims = user.custom_claims or {}

        # Si el llamador es Psicólogo, validar que el usuario pertenece a su tenant
        if caller_role == ROLE_PSICOLOGO:
            if claims.get("tenantId") != caller_tenant_id:
                raise https_fn.HttpsError(
                    https_fn.FunctionsErrorCode.PERMISSION_DENIED,
                    "Acceso denegado: el usuario no pertenece a tu organización."
                )

        if team:
            claims['team'] = team
        else:
            claims.pop('team', None)

        auth.set_custom_user_claims(uid, claims)

        _log_audit(
            action="UPDATE_USER_TEAM",
            actor_uid=req.auth.uid,
            target=uid,
            details={"new_team": team or "(sin equipo)", "email": user.email}
        )
        return {"status": "success", "message": "Plantilla actualizada con éxito."}
    except https_fn.HttpsError:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==============================================================================
# SUBSCRIPTION MANAGEMENT (Control de Acceso por Suscripción)
# ==============================================================================

@scheduler_fn.on_schedule(schedule="every 24 hours")
def check_expired_subscriptions(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Cron diario: verifica suscripciones y bloquea automáticamente cuentas expiradas.

    Flujo:
    1. Lee todos los documentos de la colección subscriptions/{uid}.
    2. Si trial_end o plan_end < hoy → añade custom_claim {blocked: true} al usuario.
    3. Si el usuario ya estaba bloqueado y su suscripción está vigente → desbloquea.
    4. Registra cada cambio en audit_log.

    Colección subscriptions/{uid}:
        plan:        "TRIAL" | "BASIC" | "PRO" | "ENTERPRISE"
        trial_end:   "YYYY-MM-DD" (solo para plan TRIAL)
        plan_end:    "YYYY-MM-DD" (para planes pagos)
        status:      "ACTIVE" | "EXPIRED" | "BLOCKED"
    """
    from firebase_admin import auth as fb_auth

    db = firestore.client()
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    print(f"[SUBSCRIPTION-CRON] Verificando suscripciones activas. Fecha: {today_str}")

    blocked_count   = 0
    unblocked_count = 0

    try:
        subs = db.collection("subscriptions").stream()
        for sub_doc in subs:
            uid  = sub_doc.id
            data = sub_doc.to_dict()

            plan      = data.get("plan", "TRIAL")
            trial_end = data.get("trial_end", "")
            plan_end  = data.get("plan_end", "")
            status    = data.get("status", "ACTIVE")

            # Determinar fecha de expiración según el tipo de plan
            expiry_date = plan_end if plan != "TRIAL" else trial_end

            if not expiry_date:
                continue  # Sin fecha de expiración → plan indefinido (ej. ENTERPRISE manual)

            is_expired = expiry_date < today_str

            try:
                user = fb_auth.get_user(uid)
                current_claims = user.custom_claims or {}
                is_currently_blocked = current_claims.get("blocked", False)

                if is_expired and not is_currently_blocked:
                    # Bloquear cuenta expirada
                    current_claims["blocked"] = True
                    fb_auth.set_custom_user_claims(uid, current_claims)
                    db.collection("subscriptions").document(uid).update({"status": "EXPIRED"})
                    _log_audit(
                        action="AUTO_BLOCK_EXPIRED",
                        actor_uid="SYSTEM",
                        target=uid,
                        details={"plan": plan, "expired_on": expiry_date, "email": user.email}
                    )
                    blocked_count += 1
                    print(f"[SUBSCRIPTION-CRON] Bloqueado: {user.email} (expiró: {expiry_date})")

                elif not is_expired and is_currently_blocked and status == "ACTIVE":
                    # Desbloquear cuenta reactivada manualmente
                    current_claims["blocked"] = False
                    fb_auth.set_custom_user_claims(uid, current_claims)
                    _log_audit(
                        action="AUTO_UNBLOCK_REACTIVATED",
                        actor_uid="SYSTEM",
                        target=uid,
                        details={"plan": plan, "plan_end": expiry_date, "email": user.email}
                    )
                    unblocked_count += 1
                    print(f"[SUBSCRIPTION-CRON] Desbloqueado: {user.email} (vigente hasta: {expiry_date})")

            except Exception as user_err:
                print(f"[SUBSCRIPTION-CRON-ERROR] Error procesando uid={uid}: {user_err}")

        print(f"[SUBSCRIPTION-CRON] Completado. Bloqueados: {blocked_count} | Desbloqueados: {unblocked_count}")

    except Exception as e:
        print(f"[SUBSCRIPTION-CRON-FATAL] Error leyendo subscriptions: {e}")


@https_fn.on_call()
def create_subscription(req: https_fn.CallableRequest) -> dict:
    """
    Crea o renueva la suscripción de un usuario. Requiere SUPER_ADMIN.

    Parámetros:
        uid:        UID del usuario en Firebase Auth
        plan:       "TRIAL" | "BASIC" | "PRO" | "ENTERPRISE"
        trial_days: Días de prueba (solo para plan TRIAL, default: 14)
        plan_days:  Días de vigencia del plan pago (default: 30)
    """
    _require_role(req, ROLES_ADMIN_ONLY)

    uid        = req.data.get("uid", "").strip()
    plan       = req.data.get("plan", "TRIAL")
    trial_days = int(req.data.get("trial_days", 14))
    plan_days  = int(req.data.get("plan_days", 30))

    if not uid:
        return {"status": "error", "message": "UID requerido."}

    valid_plans = {"TRIAL", "BASIC", "PRO", "ENTERPRISE"}
    if plan not in valid_plans:
        return {"status": "error", "message": f"Plan inválido: '{plan}'. Planes válidos: {valid_plans}"}

    from firebase_admin import auth as fb_auth
    db = firestore.client()

    try:
        user = fb_auth.get_user(uid)

        today = datetime.datetime.now(datetime.timezone.utc).date()
        sub_data = {"plan": plan, "status": "ACTIVE", "created_at": firestore.SERVER_TIMESTAMP}

        if plan == "TRIAL":
            end_date = today + datetime.timedelta(days=trial_days)
            sub_data["trial_end"] = end_date.strftime("%Y-%m-%d")
            sub_data["plan_end"]  = ""
        else:
            end_date = today + datetime.timedelta(days=plan_days)
            sub_data["plan_end"]  = end_date.strftime("%Y-%m-%d")
            sub_data["trial_end"] = ""

        db.collection("subscriptions").document(uid).set(sub_data, merge=True)

        # Desbloquear cuenta si estaba bloqueada (re-activación de suscripción)
        current_claims = user.custom_claims or {}
        if current_claims.get("blocked", False):
            current_claims["blocked"] = False
            fb_auth.set_custom_user_claims(uid, current_claims)

        _log_audit(
            action="CREATE_SUBSCRIPTION",
            actor_uid=req.auth.uid,
            target=uid,
            details={"plan": plan, "end_date": end_date.strftime("%Y-%m-%d"), "email": user.email}
        )
        return {
            "status":   "success",
            "message":  f"Suscripción {plan} creada para {user.email}. Vigente hasta: {end_date}.",
            "plan":     plan,
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
    except https_fn.HttpsError:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


@https_fn.on_call()
def update_subscription_status(req: https_fn.CallableRequest) -> dict:
    """
    Bloquea o desbloquea manualmente la cuenta de un usuario. Requiere SUPER_ADMIN.
    Útil para suspensiones manuales o reactivaciones urgentes.

    Parámetros:
        uid:     UID del usuario
        blocked: true para bloquear, false para desbloquear
        reason:  Motivo de la acción (opcional, para audit log)
    """
    _require_role(req, ROLES_ADMIN_ONLY)

    from firebase_admin import auth as fb_auth

    uid     = req.data.get("uid", "").strip()
    blocked = req.data.get("blocked", True)
    reason  = req.data.get("reason", "Acción manual del administrador")

    if not uid:
        return {"status": "error", "message": "UID requerido."}

    try:
        user   = fb_auth.get_user(uid)
        claims = user.custom_claims or {}
        claims["blocked"] = bool(blocked)
        fb_auth.set_custom_user_claims(uid, claims)

        action = "MANUAL_BLOCK" if blocked else "MANUAL_UNBLOCK"
        _log_audit(
            action=action,
            actor_uid=req.auth.uid,
            target=uid,
            details={"email": user.email, "reason": reason}
        )
        estado = "bloqueada" if blocked else "desbloqueada"
        return {"status": "success", "message": f"Cuenta {user.email} {estado} exitosamente."}
    except https_fn.HttpsError:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


@https_fn.on_call()
def register_new_tenant(req: https_fn.CallableRequest) -> dict:
    """Registra un nuevo inquilino (tenant) y crea su cuenta de acceso. Acceso público."""
    from firebase_admin import auth as fb_auth
    import random
    import string

    db = firestore.client()

    tenant_id = req.data.get("tenantId", "").strip().lower()
    # Limpiar ID
    tenant_id = "".join(c for c in tenant_id if c.isalnum())
    name = req.data.get("name", "").strip()
    email = req.data.get("email", "").strip()
    password = req.data.get("password", "")
    plan = req.data.get("plan", "BASIC")

    if not tenant_id or not name or not email or not password:
        return {"status": "error", "message": "Todos los campos son requeridos."}

    # 1. Validar unicidad del Tenant
    tenant_ref = db.collection("tenants").document(tenant_id)
    if tenant_ref.get().exists:
        return {"status": "error", "message": f"El identificador '{tenant_id}' ya está registrado."}

    try:
        # 2. Crear usuario en Firebase Auth
        user = fb_auth.create_user(email=email, password=password)

        # 3. Asignar Custom Claims
        claims = {"role": "PSICOLOGO", "tenantId": tenant_id}
        fb_auth.set_custom_user_claims(user.uid, claims)

        # 4. Generar código de asociación de 6 caracteres alfanuméricos
        chars = string.ascii_uppercase + string.digits
        association_code = "".join(random.choice(chars) for _ in range(6))

        # Calcular fecha de expiración
        today = datetime.datetime.now()
        expiration = ""
        if plan == "TRIAL":
            expiration = (today + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        elif plan in ["BASIC", "PRO"]:
            expiration = (today + datetime.timedelta(days=30)).strftime("%Y-%m-%d")

        # 5. Crear el documento del inquilino en Firestore
        tenant_ref.set({
            "id": tenant_id,
            "name": name,
            "plan": plan,
            "expiration": expiration,
            "status": "ACTIVE",
            "admin_email": email,
            "associationCode": association_code,
            "created_at": datetime.datetime.now()
        })

        return {
            "status": "success", 
            "message": f"Registro exitoso. Tu código de asociación es {association_code}."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
