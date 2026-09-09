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
# MÓDULO 2: Z-SCORES (Ventana por N Registros Válidos — Protocolo Híbrido)
# ══════════════════════════════════════════════════════════════════════════════

# ─── Parámetros del Protocolo Híbrido de Monitoreo Discontinuo (v3.3) ─────────
# Fundamento: Rubilar (2026) — Protocolo Híbrido Validado
# REQ-01: Ventana histórica N=7 sesiones válidas para eliminar el 'efecto ancla'.
# REQ-02: Media Móvil Exponencial (EMA) con alpha=0.35 (las últimas 3 sesiones ≈ 72.5% del peso).
# REQ-03: Control de Inflación de Varianza: Cap de sigma_basal en 18.84 ms (MDC).
# Test 3: Falla Grácil / Cold Start: SMA progresivo para 3 <= n < 7, transición a EMA para n >= 7.
ROLLING_BASELINE_N       =  7   # Últimas N sesiones válidas (con tau_ms) para la línea base
ROLLING_BASELINE_MIN     =  3   # Mínimo de registros para activar Z-Score (SMA provisional)
ROLLING_BASELINE_BUFFER  = ROLLING_BASELINE_N * 5  # Buffer amplio de lectura para filtrar
EMA_ALPHA                = 0.35 # Factor de suavizado exponencial (3 sesiones ≈ 72.5% del peso)
SIGMA_CAP_MAX            = 18.84# Cambio Detectable Mínimo (MDC) en ms como techo máximo de varianza
SIGMA_FLOOR_MIN          =  5.0 # Floor clínico de seguridad para evitar división por cero
# ──────────────────────────────────────────────────────────────────────────────

def compute_zscores(db, athlete_id: str, today_str: str,
                    tau_today: float, wellness_today: float | None) -> dict:
    """
    Calcula Z-Scores de τ y Wellness vs. línea base individual del atleta.

    Z = (X_hoy - X̄_basal) / SD_basal

    PROTOCOLO HÍBRIDO v3.3:
    La ventana usa los últimos ROLLING_BASELINE_N (=7) registros con tau_ms VÁLIDO.
    - REQ-01: N=7 sesiones válidas para eliminar la inercia del SMA de 15 días.
    - REQ-02: Para n >= 7 se utiliza Media Móvil Exponencial (EMA, alpha=0.35).
    - REQ-03: Clamping de sigma_basal con techo en 18.84 ms (MDC) para prevenir
              inflación de varianza que enmascare deterioros neurocognitivos agudos.
    - Falla Grácil: Si 3 <= n < 7, se aplica SMA provisional hasta completar N=7.

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
        dict con tau_zscore, wellness_zscore, baseline stats y campos de trazabilidad
    """
    try:
        # Leer un buffer amplio de Daily_Performance (sin cutoff de fecha).
        # Filtramos luego por presencia de tau_ms para obtener solo registros válidos.
        # PROTOCOLO HÍBRIDO: sin límite de fecha — tomamos los N últimos registros válidos.
        docs = (
            db.collection("Daily_Performance")
            .where("athleteId", "==", athlete_id)
            .where("date", "<", today_str)
            .order_by("date", direction=firestore.Query.DESCENDING)
            .limit(ROLLING_BASELINE_BUFFER)
            .stream()
        )

        tau_history      = []
        wellness_history = []

        for doc in docs:
            d = doc.to_dict()
            aa = d.get("advanced_analysis", {})
            tau_val = aa.get("tau_ms")
            # Solo añadir si tau_ms es válido Y aún no alcanzamos el límite N
            if tau_val and len(tau_history) < ROLLING_BASELINE_N:
                tau_history.append(float(tau_val))
            # Wellness: acumular hasta ROLLING_BASELINE_N (misma ventana para coherencia)
            w = d.get("wellness")
            if isinstance(w, dict) and len(wellness_history) < ROLLING_BASELINE_N:
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
            "tau_zscore":                    None,
            "wellness_zscore":               None,
            "tau_baseline_n":                len(tau_history),
            "tau_baseline_mean":             None,
            "tau_baseline_sd":               None,
            "tau_baseline_sigma_capped":     False,
            # ── Campos de trazabilidad del Protocolo Híbrido v3.3 ──
            "rolling_baseline_mode":         "EMA_N7_CAPPED",
            "rolling_baseline_n_requested":  ROLLING_BASELINE_N,
            "rolling_baseline_min_required": ROLLING_BASELINE_MIN,
            "rolling_baseline_alpha":        EMA_ALPHA,
            "rolling_baseline_sigma_cap":    SIGMA_CAP_MAX,
        }

        # ── Z-score de τ ──
        # Protocolo Híbrido v3.3:
        # Si len(tau_history) < 3: INSUFFICIENT_DENSITY (fallback a umbral absoluto)
        # Si 3 <= len(tau_history) < 7: SMA progresivo provisional (Test 3)
        # Si len(tau_history) >= 7: EMA(alpha=0.35) + Sigma Cap(18.84ms)
        if len(tau_history) >= ROLLING_BASELINE_MIN:
            n = len(tau_history)
            sigma_capped = False

            if n >= ROLLING_BASELINE_N:
                # REQ-02: EMA cronológica desde la sesión más antigua a la más reciente de la ventana
                # tau_history viene en orden descendente [t_-1, t_-2, ..., t_-7]
                chrono_taus = tau_history[::-1]
                ema = chrono_taus[0]
                for t in chrono_taus[1:]:
                    ema = (t * EMA_ALPHA) + (ema * (1.0 - EMA_ALPHA))
                tau_basal = ema
                mode = "EMA_N7_CAPPED"
                status_label = "CALIBRATED_EMA"
            else:
                # Test 3: SMA progresivo provisional hasta completar ventana N=7
                tau_basal = float(np.mean(tau_history))
                mode = "SMA_PROVISIONAL"
                status_label = "CALIBRATED_PROVISIONAL"

            # Estimador de varianza poblacional con prior Bayesiano para estabilización
            sample_var = float(np.var(tau_history, ddof=1)) if n > 1 else 0.0
            prior_var = 15.0 ** 2  # Varianza poblacional esperada para τ
            prior_n = 3            # Peso del prior
            posterior_var = ((n - 1) * sample_var + prior_n * prior_var) / ((n - 1) + prior_n)
            tau_sd = math.sqrt(posterior_var)

            # REQ-03: Control de Inflación de Varianza (Cap de Desviación Estándar)
            if tau_sd > SIGMA_CAP_MAX:
                tau_sd = SIGMA_CAP_MAX
                sigma_capped = True

            # Floor clínico de seguridad
            tau_sd = max(tau_sd, SIGMA_FLOOR_MIN)

            if tau_today is not None:
                result["tau_zscore"] = round((tau_today - tau_basal) / tau_sd, 3)

            result["tau_baseline_mean"]         = round(tau_basal, 2)
            result["tau_baseline_sd"]           = round(tau_sd, 2)
            result["tau_baseline_status"]       = status_label
            result["tau_baseline_sigma_capped"] = sigma_capped
            result["rolling_baseline_mode"]     = mode
            result["rolling_baseline_alpha"]    = EMA_ALPHA if mode == "EMA_N7_CAPPED" else None

            log.info(f"  τ Z-score: {result.get('tau_zscore')} (base μ={tau_basal:.1f}ms SD={tau_sd:.1f}ms, n={n}, mode={mode}, capped={sigma_capped})")
        else:
            result["tau_baseline_status"] = "INSUFFICIENT_DENSITY"
            result["rolling_baseline_mode"] = "CALIBRATING"
            log.info(f"  Insuficiente historial τ para Z-score ({len(tau_history)}/{ROLLING_BASELINE_MIN} mín requerido — Protocolo Híbrido)")

        # ── Z-score de Wellness ──
        if wellness_today is not None and len(wellness_history) >= ROLLING_BASELINE_MIN:
            w_mean = float(np.mean(wellness_history))
            n_w = len(wellness_history)
            sample_var_w = float(np.var(wellness_history, ddof=1)) if n_w > 1 else 0.0
            
            prior_var_w = 10.0 ** 2 # Varianza poblacional esperada para Wellness
            prior_n_w = 3
            posterior_var_w = ((n_w - 1) * sample_var_w + prior_n_w * prior_var_w) / ((n_w - 1) + prior_n_w)
            w_sd = math.sqrt(posterior_var_w)
            w_sd = max(w_sd, 2.0) # Floor variance para wellness
            
            result["wellness_zscore"] = round((wellness_today - w_mean) / w_sd, 3)
            log.info(f"  Wellness Z-score: {result['wellness_zscore']:.2f} (base μ={w_mean:.1f} SD={w_sd:.1f}, n={len(wellness_history)})")

        return result

    except Exception as e:
        log.error(f"Error calculando Z-scores para {athlete_id}: {e}")
        return {"tau_zscore": None, "wellness_zscore": None, "tau_baseline_n": 0}


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 3: LÓGICA DE SEMÁFORO EX-GAUSSIANO Y MOTOR PIFC
# ══════════════════════════════════════════════════════════════════════════════

PIFC_PROTOCOLS = {
    "YELLOW": {
        "title": "Protocolo Alerta Temprana",
        "interventions": [
            "Reducir carga táctica compleja (toma de decisiones) en un 20-30%",
            "Implementar NSDR (Non-Sleep Deep Rest) de 20 min post-entrenamiento",
            "Revisar higiene lumínica: bloquear luz azul 2h antes del sueño"
        ]
    },
    "ORANGE": {
        "title": "Protocolo Intervención Proactiva",
        "interventions": [
            "Reducir carga total de entrenamiento 30-40% por 48-72h",
            "Respiración de coherencia cardíaca (0.1 Hz, 5s inhala / 5s exhala)",
            "Optimizar sueño profundo: temperatura ambiente 18-19°C, oscuridad total"
        ]
    },
    "RED": {
        "title": "Protocolo Alerta Crítica — Intervención Inmediata",
        "interventions": [
            "SUSPENDER actividades de alta demanda cognitiva por 24-48h mínimo",
            "Sesión de recuperación activa únicamente (movilidad, agua termal)",
            "Evaluación clínica por psicólogo: descartar sobreentrenamiento sistémico"
        ]
    }
}

def classify_exgauss_status(tau_zscore: float | None, wellness_zscore: float | None,
                             tau_ms: float | None, lapses_count: int = 0) -> dict:
    """
    Semáforo de estado basado en distribución Ex-Gaussiana y Motor PIFC.
    Incluye la Regla de Sobrescritura Forzada por Lapses (Lapse Hard-Override Rule — Patch v2.2).
    """
    def _get_raw_status():
        # ── 1. Safety Override: Wellness Crítico ────────────────────────────────
        if wellness_zscore is not None and wellness_zscore < -2.0:
            return {
                "readiness_status": "RED",
                "fatigue_label": "Fatiga Consolidada",
                "exg_alert": (
                    f"🔴 ESTRÉS/FATIGA CRÍTICA SUBJETIVA: El bienestar se encuentra extremadamente degradado "
                    f"({abs(wellness_zscore):.1f}σ bajo la línea base). Alerta preventiva de sobreentrenamiento."
                )
            }

        # ── Fallback por τ absoluto (sin línea base histórica aún) ──────────────
        if tau_zscore is None:
            if tau_ms is None:
                return {
                    "readiness_status": "CALIBRATING",
                    "fatigue_label": "Calibrando",
                    "exg_alert": "Sin datos suficientes para clasificar. Se requieren mínimo 3 sesiones históricas."
                }
            # Umbrales clínicos absolutos (Lim & Dinges 2008) — mapeados a 4 niveles
            if tau_ms > 90:
                return {"readiness_status": "RED",    "fatigue_label": "Fatiga Consolidada",
                        "exg_alert": "🔴 Cola atencional (τ) crítica. Fatiga central probable. (Modo: Umbral Absoluto)"}
            if tau_ms > 70:
                return {"readiness_status": "ORANGE", "fatigue_label": "Fatiga en Proceso",
                        "exg_alert": "🟠 Cola atencional (τ) elevada. Intervención proactiva recomendada. (Modo: Umbral Absoluto)"}
            if tau_ms > 55:
                return {"readiness_status": "YELLOW", "fatigue_label": "Fatiga Incipiente",
                        "exg_alert": "🟡 Cola atencional (τ) en zona de precaución. (Modo: Umbral Absoluto)"}
            return {"readiness_status": "GREEN", "fatigue_label": "Homeostasis",
                    "exg_alert": "🟢 Cola atencional (τ) dentro del rango normal."}

        # ── 2. RED: Cola Atencional Crítica pura (τ_zscore > 2.0) ───────────────
        if tau_zscore > 2.0:
            return {
                "readiness_status": "RED",
                "fatigue_label": "Fatiga Consolidada",
                "exg_alert": (
                    f"🔴 FATIGA CONSOLIDADA: τ desviado {tau_zscore:.1f}σ sobre línea base. "
                    f"Los lapsos involuntarios superan el umbral de seguridad clínica. "
                    f"Intervención inmediata recomendada."
                )
            }

        # ── 3. RED: Fatiga Central Confirmada (cruce τ + wellness) ──────────────
        if tau_zscore > 1.5 and wellness_zscore is not None and wellness_zscore < -1.2:
            return {
                "readiness_status": "RED",
                "fatigue_label": "Fatiga Consolidada",
                "exg_alert": (
                    f"🔴 FATIGA CENTRAL CONFIRMADA: La cola atencional (τ) se ha desplazado "
                    f"{tau_zscore:.1f}σ sobre la línea base individual, combinada con un estado "
                    f"de bienestar {abs(wellness_zscore):.1f}σ bajo el promedio. "
                    f"El atleta está rindiendo forzadamente. Riesgo de lesión elevado."
                )
            }

        # ── 4. ORANGE: Fatiga en Proceso (1.5 ≤ τ_zscore ≤ 2.0) ────────────────
        if tau_zscore >= 1.5:
            w_info = f" | Bienestar {wellness_zscore:.1f}σ" if wellness_zscore is not None else ""
            return {
                "readiness_status": "ORANGE",
                "fatigue_label": "Fatiga en Proceso",
                "exg_alert": (
                    f"🟠 FATIGA EN PROCESO: τ elevado {tau_zscore:.1f}σ sobre línea base{w_info}. "
                    f"Reducir carga táctica y aplicar técnicas de desactivación neuropsicológica. "
                    f"Monitoreo intensivo recomendado."
                )
            }

        # ── 5. YELLOW: Fatiga Incipiente (1.0 ≤ τ_zscore < 1.5 o wellness bajo) ─
        if tau_zscore > 1.0 or (wellness_zscore is not None and wellness_zscore < -0.8):
            tau_info = f"τ elevado ({tau_zscore:.1f}σ sobre base)" if tau_zscore is not None else "Bienestar subjetivo degradado"
            w_info   = f" | Bienestar {wellness_zscore:.1f}σ bajo base" if wellness_zscore is not None else ""
            return {
                "readiness_status": "YELLOW",
                "fatigue_label": "Fatiga Incipiente",
                "exg_alert": (
                    f"🟡 ALERTA TEMPRANA: {tau_info}{w_info}. "
                    f"Monitorear carga y calidad del sueño. Revisar higiene lumínica y rutinas de recuperación."
                )
            }

        # ── 6. GREEN: Homeostasis ────────────────────────────────────────────────
        return {
            "readiness_status": "GREEN",
            "fatigue_label": "Homeostasis",
            "exg_alert": "🟢 Cola atencional dentro del rango óptimo individual. Sin intervención necesaria."
        }

    status_dict = _get_raw_status()
    status_color = status_dict.get("readiness_status", "GREEN")
    lapse_override_applied = False
    lapse_override_reason = None

    # ── HARD-RULE DE LAPSES (Patch v2.2) ───────────────────────────────────────
    # Prioridad absoluta: Elimina falsos negativos diagnósticos cuando hay bloqueos atencionales
    if lapses_count >= 2:
        if status_color in ["GREEN", "YELLOW"]:
            status_color = "ORANGE"
            lapse_override_applied = True
            lapse_override_reason = "CRITICAL_LAPSES_DETECTED"
            status_dict["fatigue_label"] = "Fatiga en Proceso (Lapses ≥ 2)"
            status_dict["exg_alert"] = (
                f"🟠 ALERTA CRÍTICA DE LAPSES: Registrados {lapses_count} bloqueos atencionales (lapses ≥ 250ms). "
                f"Estado elevado automáticamente a ORANGE por seguridad neurobiológica."
            )
    elif lapses_count == 1:
        if status_color == "GREEN":
            status_color = "YELLOW"
            lapse_override_applied = True
            lapse_override_reason = "SINGLE_LAPSE_OVERRIDE"
            status_dict["fatigue_label"] = "Fatiga Incipiente (Lapse = 1)"
            status_dict["exg_alert"] = (
                f"🟡 ALERTA PREVENTIVA DE LAPSE: Registrado 1 bloqueo atencional (lapse ≥ 250ms). "
                f"Estado elevado automáticamente de GREEN a YELLOW por presencia de fallo atencional."
            )

    status_dict["readiness_status"] = status_color
    status_dict["lapse_override_applied"] = lapse_override_applied
    status_dict["lapse_override_reason"] = lapse_override_reason

    rs = status_dict.get("readiness_status")
    if rs in PIFC_PROTOCOLS:
        status_dict["pifc_protocol"] = PIFC_PROTOCOLS[rs]
    else:
        status_dict.pop("pifc_protocol", None)

    return status_dict


def _parse_trials(trials):
    valid_trials = []
    for t in trials:
        try:
            valid_trials.append(float(t))
        except (ValueError, TypeError):
            pass
    return valid_trials


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
                    "trials":      _parse_trials(trials),
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
    PROTOCOLO HÍBRIDO v2.1: Rolling baseline por N registros válidos.
    """
    athlete_id   = measurement["athlete_id"]
    athlete_name = measurement["athlete_name"]
    trials       = measurement["trials"]
    wellness_raw = measurement["wellness"]

    # ── Leer baseline_context del documento del atleta ──
    # Este campo es seteado por el psicólogo al dar de alta al deportista.
    # No altera el cálculo matemático — se almacena como metadato de trazabilidad.
    baseline_context = "UNKNOWN"
    try:
        ath_snap = db.collection("athletes").document(athlete_id).get()
        if ath_snap.exists:
            baseline_context = ath_snap.to_dict().get("baseline_context", "UNKNOWN")
    except Exception:
        pass  # No bloquear el análisis si falla la lectura del campo

    log.info(f"\n{'─'*60}")
    log.info(f"Procesando: {athlete_name} ({athlete_id}) | baseline_context: {baseline_context}")

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

    # ── 4. Extraer Lapses y Clasificar Semáforo (Patch v2.2) ──
    lapses_count = measurement.get("lapses")
    if lapses_count is None:
        pvt_m = measurement.get("pvt") or {}
        if isinstance(pvt_m, dict):
            metrics_m = pvt_m.get("metrics") or {}
            lapses_count = metrics_m.get("lapses") if isinstance(metrics_m, dict) else None
            if lapses_count is None:
                lapses_count = pvt_m.get("lapses")
    if lapses_count is None:
        lapses_count = len([t for t in trials if t >= 500.0]) if trials else 0
    else:
        try:
            lapses_count = int(lapses_count)
        except (ValueError, TypeError):
            lapses_count = len([t for t in trials if t >= 500.0]) if trials else 0

    status = classify_exgauss_status(
        tau_zscore=zscores.get("tau_zscore"),
        wellness_zscore=zscores.get("wellness_zscore"),
        tau_ms=tau_today,
        lapses_count=lapses_count
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

        # Z-Scores (Protocolo Híbrido — N registros válidos)
        "tau_zscore":           zscores.get("tau_zscore"),
        "wellness_zscore":      zscores.get("wellness_zscore"),
        "tau_baseline_n":       zscores.get("tau_baseline_n"),
        "tau_baseline_mean_ms":        zscores.get("tau_baseline_mean"),
        "tau_baseline_sd_ms":          zscores.get("tau_baseline_sd"),
        "tau_baseline_status":         zscores.get("tau_baseline_status"),
        "tau_baseline_sigma_capped":   zscores.get("tau_baseline_sigma_capped", False),
        # Trazabilidad del Protocolo Híbrido v3.3
        "rolling_baseline_mode":         zscores.get("rolling_baseline_mode"),
        "rolling_baseline_n_requested":  zscores.get("rolling_baseline_n_requested"),
        "rolling_baseline_n_actual":     zscores.get("tau_baseline_n"),
        "rolling_baseline_min_required": zscores.get("rolling_baseline_min_required"),
        "rolling_baseline_alpha":        zscores.get("rolling_baseline_alpha"),
        "rolling_baseline_sigma_cap":    zscores.get("rolling_baseline_sigma_cap"),
        "baseline_context":              baseline_context,

        # Resultado del semáforo y Trazabilidad de Lapses (Patch v2.2)
        "readiness_status":       status["readiness_status"],
        "fatigue_label":          status.get("fatigue_label"),
        "exg_alert":              status["exg_alert"],
        "lapse_override_applied": status.get("lapse_override_applied", False),
        "lapse_override_reason":  status.get("lapse_override_reason", None),

        # Metadatos de trazabilidad (M-04)
        "wellness_source":  wellness_source,
        "wellness_score":   round(wellness_score, 2) if wellness_score is not None else None,
        "processed_at":     firestore.SERVER_TIMESTAMP,
        "version":          "exgauss-3.3",     # v3.3: N=7 Rolling Baseline + EMA(alpha=0.35) + Sigma Cap(18.84ms)
        "pvt_protocol":     "PVT-B-30"
    }

    # ── 6. Write-back a Firestore ──
    doc_id = f"{athlete_id}_{today_str}"
    
    tenant_id = measurement.get("tenant_id") or measurement.get("tenantId")
    if not tenant_id:
        try:
            ath_snap = db.collection("athletes").document(athlete_id).get()
            if ath_snap.exists:
                tenant_id = ath_snap.to_dict().get("tenantId")
        except Exception:
            pass

    write_payload = {
        "advanced_analysis": advanced_analysis,
        "athleteId": athlete_id,
        "athleteName": athlete_name,
        "date": today_str,
    }
    if tenant_id:
        write_payload["tenantId"] = tenant_id

    db.collection("Daily_Performance").document(doc_id).set(
        write_payload,
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
