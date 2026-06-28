"""
╔══════════════════════════════════════════════════════════════════╗
║   IMED SPORT — pvt_exgauss_worker.py                            ║
║   Motor de Análisis Ex-Gaussiano & Z-Scores (PVT-B, n≥30)      ║
║   Versión: 2.0.0 | Cloud Functions (Event-Driven, Serverless)   ║
║                                                                  ║
║   Fundamento científico:                                         ║
║   - Hohle (1965) / Ratcliff & Murdock (1976): Ex-Gaussian PVT  ║
║   - Basner & Dinges (2011): Validación PVT-B (30 estímulos)     ║
║   - Lim & Dinges (2008): τ como predictor de lapses cognitivos  ║
║                                                                  ║
║   Arquitectura: Importado como módulo por main.py               ║
║   Trigger: @firestore_fn.on_document_created                    ║
║   Región: us-central1 | Python 3.13 | Memory: 512MB             ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import json
import math
import logging
from datetime import datetime, timedelta, timezone

import numpy as np
from scipy.stats import exponnorm
from scipy.optimize import minimize
import firebase_admin
from firebase_admin import credentials, firestore

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s — %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("IMED-ExGauss")

# ─── Firebase Init ─────────────────────────────────────────────────────────────
def init_firebase():
    """Inicializa Firebase Admin con Service Account o credenciales implícitas de entorno (ADC).
    En Cloud Functions (GCP) las credenciales se inyectan automáticamente — no se requiere archivo.
    """
    if not firebase_admin._apps:
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            log.info(f"Firebase inicializado con Service Account: {cred_path}")
        else:
            # Credenciales implícitas de GCP (Application Default Credentials)
            firebase_admin.initialize_app()
            log.info("Firebase inicializado con credenciales de entorno (ADC — GCP/Cloud Functions)")
    return firestore.client()


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 1: AJUSTE EX-GAUSSIANO
# ══════════════════════════════════════════════════════════════════════════════

def fit_exgaussian(trials: list[float]) -> dict | None:
    """
    Ajusta la distribución Ex-Gaussiana sobre el vector de tiempos de reacción.

    La distribución Ex-Gaussiana = Normal(μ, σ) ⊕ Exponencial(τ)
    Parámetros estimados por Maximum Likelihood Estimation acotada y penalizada.

    Args:
        trials: Lista de tiempos de reacción en ms (n ≥ 20 recomendado, ≥ 30 óptimo)

    Returns:
        dict con μ, σ, τ y métricas de calidad del ajuste, o None si falla.
    """
    # Ajuste de élite: Límite inferior 100ms (límite fisiológico real).
    # 120ms descartaba tiempos excepcionales válidos.
    trials_arr = np.array([t for t in trials if 100 <= t <= 1000], dtype=float)
    n = len(trials_arr)

    if n < 20:
        log.warning(f"Insuficientes trials válidos: {n} (mínimo 20)")
        return None

    try:
        # Inicialización por Método de Momentos para estabilidad
        mean_val = np.mean(trials_arr)
        var_val = np.var(trials_arr, ddof=1)
        m3 = np.mean((trials_arr - mean_val)**3)

        tau_init = (m3 / 2.0)**(1/3) if m3 > 0 else 0.2 * np.sqrt(var_val)
        tau_init = min(tau_init, np.sqrt(var_val) * 0.9)
        sigma_init = np.sqrt(max(1.0, var_val - tau_init**2))
        mu_init = mean_val - tau_init

        mu_init    = np.clip(mu_init,    100.0, 400.0)
        sigma_init = np.clip(sigma_init,   5.0, 200.0)
        # Límite inferior de τ elevado a 20ms (poblaciones descansadas τ ≥ 20ms; Lim & Dinges 2008)
        tau_init   = np.clip(tau_init,    20.0, 300.0)

        # Función objetivo acotada y regularizada
        def neg_log_likelihood(params):
            mu, sigma, tau = params
            K = tau / sigma
            log_pdf = exponnorm.logpdf(trials_arr, K, loc=mu, scale=sigma)
            nll = -np.sum(log_pdf)
            if np.isnan(nll) or np.isinf(nll):
                return 1e10
            # Penalización L2 (Ridge/Tikhonov) hacia medias poblacionales teóricas
            # Ancora μ→220ms, σ→45ms, τ→65ms (deportistas de élite en reposo)
            return nll + 0.001 * (mu - 220)**2 + 0.01 * (sigma - 45)**2 + 0.005 * (tau - 65)**2

        bounds = [(100.0, 450.0), (10.0, 250.0), (20.0, 350.0)]

        res = minimize(
            neg_log_likelihood,
            x0=[mu_init, sigma_init, tau_init],
            method='L-BFGS-B',
            bounds=bounds,
            options={'ftol': 1e-6}
        )

        if not res.success:
            log.warning("Optimización acotada falló. Usando fallback estándar.")
            K, loc, scale = exponnorm.fit(trials_arr)
            mu, sigma, tau = loc, scale, K * scale
        else:
            mu, sigma, tau = res.x

        mu_ms, sigma_ms, tau_ms = float(mu), float(sigma), float(tau)

        exg_mean = mu_ms + tau_ms

        log_lik = float(np.sum(exponnorm.logpdf(trials_arr, tau_ms / sigma_ms, loc=mu_ms, scale=sigma_ms)))

        if not (100 <= mu_ms <= 450) or sigma_ms <= 0 or tau_ms <= 0:
            log.warning(f"Parámetros Ex-Gaussianos fuera de rango clínico: μ={mu_ms:.1f}, σ={sigma_ms:.1f}, τ={tau_ms:.1f}")
            return None

        # ── AIC / BIC (L-03) ──────────────────────────────────────────────────
        # AIC = 2k - 2·ln(L);  BIC = k·ln(n) - 2·ln(L)   | k=3 parámetros
        k = 3
        aic = round(2 * k - 2 * log_lik, 3)
        bic = round(k * math.log(n) - 2 * log_lik, 3)

        # ── Bondad de Ajuste: Anderson-Darling (M-03) ─────────────────────────
        # Genera muestras teóricas de la Ex-Gaussiana ajustada y aplica KS-test
        # para detectar bimodalidad o ajuste pobre (sesiones con fatiga extrema).
        from scipy.stats import kstest, anderson
        cdf_fn = lambda x: exponnorm.cdf(x, tau_ms / sigma_ms, loc=mu_ms, scale=sigma_ms)
        ks_stat, ks_pval = kstest(trials_arr, cdf_fn)
        # p < 0.05 indica que la distribución observada difiere significativamente
        # de la Ex-Gaussiana ajustada (posible bimodalidad por fatiga extrema)
        fit_quality = "POOR" if ks_pval < 0.05 else "ACCEPTABLE" if ks_pval < 0.20 else "GOOD"
        if fit_quality == "POOR":
            log.warning(f"  ⚠ Bondad de ajuste POBRE (KS p={ks_pval:.3f}). Posible distribución bimodal — τ puede ser impreciso.")

        result = {
            "mu_ms":       round(mu_ms, 2),
            "sigma_ms":    round(sigma_ms, 2),
            "tau_ms":      round(tau_ms, 2),
            "exg_mean_ms": round(exg_mean, 2),
            "n_trials":    int(n),
            "log_lik":     round(log_lik, 3),
            "aic":         aic,
            "bic":         bic,
            "fit_quality": fit_quality,
            "ks_pval":     round(float(ks_pval), 4),
        }
        log.info(f"  Ex-Gauss ajustado: μ={mu_ms:.1f}ms  σ={sigma_ms:.1f}ms  τ={tau_ms:.1f}ms (n={n}) | AIC={aic} | Fit={fit_quality}")
        return result

    except Exception as e:
        log.error(f"Error en ajuste Ex-Gaussiano: {e}")
        import traceback
        traceback.print_exc()
        return None


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 2: Z-SCORES (Ventana 21 días)
# ══════════════════════════════════════════════════════════════════════════════

def compute_zscores(db, athlete_id: str, today_str: str,
                    tau_today: float, wellness_today: float | None) -> dict:
    """
    Calcula Z-Scores de τ y Wellness vs. línea base individual de 21 días.

    Z = (X_hoy - X̄_21d) / SD_21d

    Interpretación de τ_zscore:
        > +1.5  → Cola atencional prolongada (ALERTA)
        > +2.0  → Fatiga central confirmada (CRÍTICO)
        < -1.0  → Rendimiento superior a la línea base

    Args:
        db:              Cliente Firestore
        athlete_id:      ID del atleta
        today_str:       Fecha de hoy (YYYY-MM-DD) — se excluye del baseline
        tau_today:       τ calculado en la sesión de hoy
        wellness_today:  Score de wellness de hoy (0-100) o None

    Returns:
        dict con tau_zscore, wellness_zscore, baseline stats
    """
    cutoff = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=21)).strftime("%Y-%m-%d")

    try:
        # Leer historial de Daily_Performance de los últimos 21 días
        docs = (
            db.collection("Daily_Performance")
            .where("athleteId", "==", athlete_id)
            .where("date", ">=", cutoff)
            .where("date", "<", today_str)
            .order_by("date", direction=firestore.Query.DESCENDING)
            .limit(30)
            .stream()
        )

        tau_history      = []
        wellness_history = []

        for doc in docs:
            d = doc.to_dict()
            aa = d.get("advanced_analysis", {})
            if aa.get("tau_ms"):
                tau_history.append(float(aa["tau_ms"]))
            w = d.get("wellness")
            if isinstance(w, dict):
                # Fórmula Wellness ponderada por evidencia (4 variables, máx 100 pts)
                # Pesos basados en literatura de ciencias del deporte:
                #   sleepHours   30 pts — mayor predictor de consolidación cognitiva (Watson et al., 2015)
                #   sleepQuality 25 pts — calidad del sueño (Lastella et al., 2020)
                #   stressLevel  25 pts — predictor primario de bienestar (Hooper & Mackinnon, 1995)
                #   fatigueLevel 20 pts — marcador complementario (Saw et al., 2016)
                # DEBE SER IDÉNTICA a snc_engine.dart y app_v411_final.js
                h = w.get("sleepHours",   8)
                q = w.get("sleepQuality", 5)
                s = w.get("stressLevel",  1)
                f = w.get("fatigueLevel", 1)
                score = (
                    (min(8, h) / 8) * 30 +  # sleep_hours    (0–30 pts)
                    (q / 5)         * 25 +  # sleep_quality  (0–25 pts)
                    ((6 - s) / 5)   * 25 +  # stress (inv.)  (0–25 pts)
                    ((6 - f) / 5)   * 20    # fatigue (inv.) (0–20 pts)
                )
                wellness_history.append(score)

        result = {
            "tau_zscore":      None,
            "wellness_zscore": None,
            "tau_baseline_n":  len(tau_history),
            "tau_baseline_mean": None,
            "tau_baseline_sd":   None,
        }

        # ── Z-score de τ ──
        if len(tau_history) >= 8:
            tau_mean = float(np.mean(tau_history))
            tau_sd   = float(np.std(tau_history, ddof=1))
            # Floor standard deviation para prevenir varianza minúscula
            tau_sd = max(tau_sd, 5.0) 
            
            if tau_today is not None:
                result["tau_zscore"]        = round((tau_today - tau_mean) / tau_sd, 3)
            result["tau_baseline_mean"] = round(tau_mean, 2)
            result["tau_baseline_sd"]   = round(tau_sd, 2)
            
            log.info(f"  τ Z-score: {result.get('tau_zscore')}  (base μ={tau_mean:.1f}ms SD={tau_sd:.1f}ms, n={len(tau_history)})")
        else:
            result["tau_baseline_status"] = "INSUFFICIENT_DENSITY"
            log.info(f"  Insuficiente historial τ para Z-score ({len(tau_history)}/8 min)")

        # ── Z-score de Wellness ──
        if wellness_today is not None and len(wellness_history) >= 8:
            w_mean = float(np.mean(wellness_history))
            w_sd   = float(np.std(wellness_history, ddof=1))
            w_sd = max(w_sd, 2.0) # Floor variance para wellness
            
            result["wellness_zscore"] = round((wellness_today - w_mean) / w_sd, 3)
            log.info(f"  Wellness Z-score: {result['wellness_zscore']:.2f}  (base μ={w_mean:.1f} SD={w_sd:.1f}, n={len(wellness_history)})")

        return result

    except Exception as e:
        log.error(f"Error calculando Z-scores para {athlete_id}: {e}")
        return {"tau_zscore": None, "wellness_zscore": None, "tau_baseline_n": 0}


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 3: LÓGICA DE SEMÁFORO EX-GAUSSIANO
# ══════════════════════════════════════════════════════════════════════════════

def classify_exgauss_status(tau_zscore: float | None, wellness_zscore: float | None,
                             tau_ms: float | None) -> dict:
    """
    Semáforo de estado basado en distribución Ex-Gaussiana.

    Reglas (orden de prioridad):
    1. Si wellness_zscore < -2.0 → ROJO (Estrés/Fatiga subjetiva crítica)
    2. Si tau_zscore > 1.5 AND wellness_zscore < -1.2 → ROJO (Fatiga Central Confirmada)
    3. Si tau_zscore > 2.0 (solo) → ROJO (Cola atencional crítica)
    4. Si tau_zscore > 1.0 OR wellness_zscore < -0.8 → AMARILLO
    5. Sin Z-scores disponibles → usar τ absoluto como fallback clínico
    6. Else → VERDE
    """
    # 1. Regla de Seguridad por Wellness Crítico (Override)
    if wellness_zscore is not None and wellness_zscore < -2.0:
        return {
            "readiness_status": "RED",
            "exg_alert": (
                f"🔴 ESTRÉS/FATIGA CRÍTICA SUBJETIVA: El bienestar se encuentra extremadamente degradado "
                f"({abs(wellness_zscore):.1f}σ bajo la línea base). Alerta preventiva de sobreentrenamiento."
            )
        }

    # Fallback por τ absoluto (sin línea base histórica aún)
    if tau_zscore is None:
        if tau_ms is None:
            return {"readiness_status": "CALIBRATING", "exg_alert": "Sin datos suficientes para clasificar."}
        # Umbrales clínicos absolutos (Lim & Dinges 2008)
        if tau_ms > 80:
            return {"readiness_status": "RED",    "exg_alert": "Cola atencional (τ) elevada. Fatiga central probable. (Modo: Umbral Absoluto)"}
        if tau_ms > 55:
            return {"readiness_status": "YELLOW", "exg_alert": "Cola atencional (τ) en zona de precaución. (Modo: Umbral Absoluto)"}
        return {"readiness_status": "GREEN", "exg_alert": "Cola atencional (τ) dentro del rango normal."}

    # Reglas Z-score
    if tau_zscore > 1.5 and wellness_zscore is not None and wellness_zscore < -1.2:
        return {
            "readiness_status": "RED",
            "exg_alert": (
                f"🔴 FATIGA CENTRAL CONFIRMADA: La cola atencional (τ) se ha desplazado "
                f"{tau_zscore:.1f}σ sobre tu línea base individual, combinada con un estado "
                f"de bienestar {abs(wellness_zscore):.1f}σ bajo tu promedio. "
                f"El atleta está rindiendoforzadamente. Riesgo de lesión elevado."
            )
        }

    if tau_zscore > 2.0:
        return {
            "readiness_status": "RED",
            "exg_alert": (
                f"🔴 COLA ATENCIONAL CRÍTICA: τ desviado {tau_zscore:.1f}σ sobre línea base. "
                f"Los lapsos involuntarios superan el umbral de seguridad clínica."
            )
        }

    if tau_zscore > 1.0 or (wellness_zscore is not None and wellness_zscore < -0.8):
        # Construir mensaje seguro — tau_zscore puede ser None si solo wellness activó la rama
        tau_info = f"τ elevado ({tau_zscore:.1f}σ sobre base)" if tau_zscore is not None else "Bienestar subjetivo degradado"
        w_info   = f" | Bienestar {wellness_zscore:.1f}σ bajo base" if wellness_zscore is not None else ""
        return {
            "readiness_status": "YELLOW",
            "exg_alert": (
                f"🟡 PRECAUCIÓN: {tau_info}{w_info}. "
                f"Monitorear carga y calidad del sueño."
            )
        }

    return {
        "readiness_status": "GREEN",
        "exg_alert": "🟢 Cola atencional dentro del rango óptimo individual."
    }


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 4: EXTRACCIÓN DE DATOS DESDE FIRESTORE
# ══════════════════════════════════════════════════════════════════════════════

def get_today_measurements(db, today_str: str) -> list[dict]:
    """
    Obtiene todos los documentos de mediciones del día actual desde
    athletes/{id}/measurements/ donde date == today_str.
    """
    measurements = []

    try:
        athletes = db.collection("athletes").stream()
        for ath_doc in athletes:
            athlete_id = ath_doc.id
            ath_data   = ath_doc.to_dict()

            # Buscar medición de hoy
            m_docs = (
                db.collection("athletes").document(athlete_id)
                .collection("measurements")
                .where("date", "==", today_str)
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(1)
                .stream()
            )

            for m_doc in m_docs:
                m = m_doc.to_dict()
                pvt = m.get("pvt", {})
                metrics = pvt.get("metrics", {})

                # Extraer raw trials — campo clave para Ex-Gaussiano
                trials = (
                    metrics.get("trials") or
                    metrics.get("rawReactionTimes") or
                    pvt.get("trials") or
                    pvt.get("logs") or
                    m.get("trials") or
                    []
                )

                measurements.append({
                    "athlete_id":  athlete_id,
                    "athlete_name": f"{ath_data.get('firstName','')} {ath_data.get('lastName','')}".strip() or athlete_id,
                    "date":        today_str,
                    "trials":      [float(t) for t in trials if isinstance(t, (int, float))],
                    "wellness":    m.get("wellness"),
                    "iri":         m.get("iri"),
                    "measurement_id": m_doc.id,
                })
                log.info(f"  → {athlete_id}: {len(trials)} trials crudos encontrados")

    except Exception as e:
        log.error(f"Error extrayendo mediciones: {e}")

    return measurements


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 5: ORQUESTADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def process_athlete(db, measurement: dict, today_str: str) -> None:
    """
    Procesa un atleta completo: Ex-Gaussiano → Z-scores → Semáforo → Write-back.
    """
    athlete_id   = measurement["athlete_id"]
    athlete_name = measurement["athlete_name"]
    trials       = measurement["trials"]
    wellness_raw = measurement["wellness"]

    log.info(f"\n{'─'*60}")
    log.info(f"Procesando: {athlete_name} ({athlete_id})")

    # ── 1. Ajuste Ex-Gaussiano ──
    exg = fit_exgaussian(trials)

    if exg is None and len(trials) < 20:
        log.warning(f"  {athlete_name}: Solo {len(trials)} trials — insuficiente para Ex-Gaussiano. Saltando.")
        # Escribir nota de calibración
        doc_id = f"{athlete_id}_{today_str}"
        db.collection("Daily_Performance").document(doc_id).set({
            "advanced_analysis": {
                "status": "INSUFFICIENT_TRIALS",
                "n_trials": len(trials),
                "message": f"Se requieren ≥20 trials (recibidos: {len(trials)}). Verifique configuración PVT.",
                "processed_at": firestore.SERVER_TIMESTAMP,
                "version": "exgauss-1.0"
            }
        }, merge=True)
        return

    # ── 2. Calcular Wellness Score (0–100) ──
    # Pesos basados en literatura (Watson 2015; Hooper 1995; Lastella 2020; Saw 2016)
    # DEBE SER IDÉNTICA a snc_engine.dart y app_v411_final.js
    wellness_score  = None
    wellness_source = "NO_WELLNESS_DATA"  # M-04: transparencia clínica
    if isinstance(wellness_raw, dict):
        h = wellness_raw.get("sleepHours",   8)
        q = wellness_raw.get("sleepQuality", 5)
        s = wellness_raw.get("stressLevel",  1)
        f = wellness_raw.get("fatigueLevel", 1)
        wellness_score = (
            (min(8, h) / 8) * 30 +  # 30 pts: sueño horas (mayor predictor cognitivo)
            (q / 5)         * 25 +  # 25 pts: calidad sueño
            ((6 - s) / 5)   * 25 +  # 25 pts: estrés percibido (inv.)
            ((6 - f) / 5)   * 20    # 20 pts: fatiga percibida (inv.)
        )
        fields_present = [k for k in ["sleepHours", "sleepQuality", "stressLevel", "fatigueLevel"] if wellness_raw.get(k) is not None]
        wellness_source = "WELLNESS_4VAR" if len(fields_present) == 4 else f"WELLNESS_PARTIAL_{len(fields_present)}VAR"

    # ── 3. Z-scores ──
    tau_today = exg["tau_ms"] if exg else None
    zscores = compute_zscores(db, athlete_id, today_str, tau_today, wellness_score)

    # ── 4. Clasificación Semáforo ──
    status = classify_exgauss_status(
        tau_zscore=zscores.get("tau_zscore"),
        wellness_zscore=zscores.get("wellness_zscore"),
        tau_ms=tau_today
    )

    # ── 5. Construir payload advanced_analysis ──
    advanced_analysis = {
        # Parámetros Ex-Gaussianos
        # NOTA C-02: El campo 'iri' en Firestore es el IRI compuesto calculado por la app
        # móvil (Wellness + PVT). No es el PVT crudo. El worker opera sobre tau_ms
        # (parámetro Ex-Gaussiano puro) para evitar doble-conteo de Wellness.
        "mu_ms":       exg["mu_ms"]       if exg else None,
        "sigma_ms":    exg["sigma_ms"]    if exg else None,
        "tau_ms":      exg["tau_ms"]      if exg else None,
        "exg_mean_ms": exg["exg_mean_ms"] if exg else None,
        "n_trials":    exg["n_trials"]    if exg else len(trials),
        "log_lik":     exg["log_lik"]     if exg else None,

        # Bondad de ajuste Ex-Gaussiano (M-03)
        "aic":         exg["aic"]         if exg else None,
        "bic":         exg["bic"]         if exg else None,
        "fit_quality": exg["fit_quality"] if exg else None,
        "ks_pval":     exg["ks_pval"]     if exg else None,

        # Z-Scores (ventana 21 días)
        "tau_zscore":           zscores.get("tau_zscore"),
        "wellness_zscore":      zscores.get("wellness_zscore"),
        "tau_baseline_n":       zscores.get("tau_baseline_n"),
        "tau_baseline_mean_ms": zscores.get("tau_baseline_mean"),
        "tau_baseline_sd_ms":   zscores.get("tau_baseline_sd"),
        "tau_baseline_status":  zscores.get("tau_baseline_status"),

        # Resultado del semáforo
        "readiness_status": status["readiness_status"],
        "exg_alert":        status["exg_alert"],

        # Metadatos de trazabilidad (M-04)
        "wellness_source":  wellness_source,   # Indica si el IRI incluyó todos los campos de Wellness
        "wellness_score":   round(wellness_score, 2) if wellness_score is not None else None,
        "processed_at":     firestore.SERVER_TIMESTAMP,
        "version":          "exgauss-2.0",     # v2.0: formula unificada + goodness-of-fit
        "pvt_protocol":     "PVT-B-30"
    }

    # ── 6. Write-back a Firestore ──
    doc_id = f"{athlete_id}_{today_str}"
    db.collection("Daily_Performance").document(doc_id).set(
        {"advanced_analysis": advanced_analysis},
        merge=True
    )

    log.info(f"  ✅ {athlete_name}: {status['readiness_status']} | τ={tau_today}ms | τ_z={zscores.get('tau_zscore')} | w_z={zscores.get('wellness_zscore')}")


def main():
    log.info("═" * 60)
    log.info("IMED SPORT — Worker Ex-Gaussiano v2.0")
    log.info(f"Ejecución: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log.info("═" * 60)

    db = init_firebase()

    # Fecha de análisis: hoy por defecto, o pasada como argumento
    import sys
    today_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log.info(f"Procesando fecha: {today_str}")

    # 1. Extraer mediciones del día
    measurements = get_today_measurements(db, today_str)
    log.info(f"\nAtletas con medición hoy: {len(measurements)}")

    if not measurements:
        log.info("Sin mediciones para procesar. Finalizando.")
        return

    # 2. Procesar cada atleta
    processed = 0
    errors     = 0
    for m in measurements:
        try:
            process_athlete(db, m, today_str)
            processed += 1
        except Exception as e:
            log.error(f"Error procesando {m['athlete_id']}: {e}")
            errors += 1

    log.info("\n" + "═" * 60)
    log.info(f"RESUMEN: {processed} atletas procesados | {errors} errores")
    log.info("═" * 60)


if __name__ == "__main__":
    main()
