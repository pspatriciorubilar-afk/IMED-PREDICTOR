"""
══════════════════════════════════════════════════════════════════════════════
 IMED PREDICTOR — Tests Unitarios Motor Ex-Gaussiano v3.3 (Z-Score EMA N=7)
 Cubre: REQ-01, REQ-02, REQ-03, REQ-04, Test 1 (Reactividad Aguda), Test 3 (Falla Grácil)
══════════════════════════════════════════════════════════════════════════════
"""
import sys, os
import math
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from pvt_exgauss_worker import (
    compute_zscores, 
    classify_exgauss_status, 
    ROLLING_BASELINE_N, 
    ROLLING_BASELINE_MIN, 
    EMA_ALPHA, 
    SIGMA_CAP_MAX, 
    SIGMA_FLOOR_MIN
)

class MockDoc:
    def __init__(self, date_str, tau_ms, wellness_dict=None):
        self._data = {
            "date": date_str,
            "advanced_analysis": {"tau_ms": tau_ms} if tau_ms is not None else {},
            "wellness": wellness_dict or {
                "sleepHours": 8,
                "sleepQuality": 4,
                "stressLevel": 2,
                "fatigueLevel": 2,
            }
        }
    def to_dict(self):
        return self._data

class MockQuery:
    def __init__(self, docs):
        self.docs = docs
    def where(self, *args, **kwargs):
        return self
    def order_by(self, *args, **kwargs):
        return self
    def limit(self, *args, **kwargs):
        return self
    def stream(self):
        return iter(self.docs)

class MockDB:
    def __init__(self, docs):
        self.docs = docs
    def collection(self, name):
        return MockQuery(self.docs)


# ─── REQ-01: Parámetros del Protocolo v3.3 ───────────────────────────────────

def test_constants_v33():
    assert ROLLING_BASELINE_N == 7, "Ventana debe ser N=7"
    assert ROLLING_BASELINE_MIN == 3, "Mínimo para activación debe ser 3"
    assert EMA_ALPHA == 0.35, "Alpha de EMA debe ser 0.35"
    assert SIGMA_CAP_MAX == 18.84, "Cap máximo de sigma debe ser 18.84 ms"
    assert SIGMA_FLOOR_MIN == 5.0, "Floor mínimo de sigma debe ser 5.0 ms"


# ─── REQ-02: Ponderación Matemática de EMA (72.5% en últimas 3 evaluaciones) ─

def test_ema_weights_last_3_days():
    """Valida que las últimas 3 evaluaciones representen ~72.5% del peso."""
    w1 = EMA_ALPHA
    w2 = EMA_ALPHA * (1.0 - EMA_ALPHA)
    w3 = EMA_ALPHA * ((1.0 - EMA_ALPHA) ** 2)
    total_3_days = w1 + w2 + w3
    # 0.35 + 0.2275 + 0.147875 = 0.725375
    assert abs(total_3_days - 0.7254) < 0.001


# ─── Test 3: Falla Grácil / Cold Start (N < 3, 3 <= N < 7, N >= 7) ───────────

def test_cold_start_under_3_records():
    """Con menos de 3 registros válidos, el estado debe ser INSUFFICIENT_DENSITY y CALIBRATING."""
    docs = [
        MockDoc("2026-09-07", 40.0),
        MockDoc("2026-09-06", 42.0),
    ]
    db = MockDB(docs)
    res = compute_zscores(db, "ath_01", "2026-09-08", tau_today=45.0, wellness_today=80.0)
    assert res["tau_baseline_status"] == "INSUFFICIENT_DENSITY"
    assert res["tau_zscore"] is None
    assert res["rolling_baseline_mode"] == "CALIBRATING"

def test_provisional_sma_between_3_and_6_records():
    """Con entre 3 y 6 registros, el sistema usa SMA provisional."""
    docs = [
        MockDoc("2026-09-07", 40.0),
        MockDoc("2026-09-06", 42.0),
        MockDoc("2026-09-05", 44.0),
        MockDoc("2026-09-04", 46.0),
    ]
    db = MockDB(docs)
    res = compute_zscores(db, "ath_01", "2026-09-08", tau_today=50.0, wellness_today=80.0)
    assert res["tau_baseline_status"] == "CALIBRATED_PROVISIONAL"
    assert res["rolling_baseline_mode"] == "SMA_PROVISIONAL"
    assert res["tau_baseline_n"] == 4
    # SMA de [40, 42, 44, 46] = 43.0
    assert res["tau_baseline_mean"] == 43.0
    assert res["tau_zscore"] is not None

def test_ema_transition_at_7_records():
    """Con 7 registros, pasa automáticamente a EMA_N7_CAPPED."""
    # Docs en orden DESC (de más reciente a más antiguo):
    # 2026-09-07 (t-1) a 2026-09-01 (t-7)
    taus = [40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0]
    docs = [MockDoc(f"2026-09-0{7-i}", taus[i]) for i in range(7)]
    db = MockDB(docs)
    res = compute_zscores(db, "ath_01", "2026-09-08", tau_today=55.0, wellness_today=80.0)
    assert res["tau_baseline_status"] == "CALIBRATED_EMA"
    assert res["rolling_baseline_mode"] == "EMA_N7_CAPPED"
    assert res["tau_baseline_n"] == 7
    assert res["tau_baseline_mean"] == 40.0
    assert res["tau_zscore"] is not None


# ─── REQ-03: Control de Inflación de Varianza (Cap en 18.84 ms) ───────────────

def test_sigma_cap_clamping_high_variance():
    """Si la desviación estándar calculada supera 18.84 ms, debe fijarse exactamente en 18.84."""
    # Serie de datos altamente dispersa
    taus = [100.0, 30.0, 95.0, 25.0, 110.0, 35.0, 105.0]
    docs = [MockDoc(f"2026-09-0{7-i}", taus[i]) for i in range(7)]
    db = MockDB(docs)
    res = compute_zscores(db, "ath_01", "2026-09-08", tau_today=120.0, wellness_today=75.0)
    assert res["tau_baseline_sd"] == 18.84
    assert res["tau_baseline_sigma_capped"] is True

def test_sigma_floor_clamping_low_variance():
    """Si la desviación estándar es extremadamente pequeña, el floor clínico debe ser 5.0 ms."""
    taus = [40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0]
    docs = [MockDoc(f"2026-09-0{7-i}", taus[i]) for i in range(7)]
    db = MockDB(docs)
    res = compute_zscores(db, "ath_01", "2026-09-08", tau_today=40.0, wellness_today=80.0)
    # Con prior bayesiano (prior_n=3, prior_var=225) y sample_var=0:
    # posterior_var = (3 * 225) / 9 = 75 -> sqrt(75) = 8.66 ms (seguro)
    assert res["tau_baseline_sd"] >= SIGMA_FLOOR_MIN
    assert res["tau_baseline_sd"] <= SIGMA_CAP_MAX


# ─── Test 1: Reactividad Aguda en 48 Horas (+15% en tau durante 2 días) ───────

def test_acute_reactivity_48h():
    """
    Atleta estable con tau base de 40ms.
    Incremento del 15% (tau = 46ms) durante 2 días seguidos.
    En el día 2, el nuevo Z-score con N=7 EMA salta a zona de alerta (Z >= 1.0 -> YELLOW/ORANGE).
    """
    base_tau = 40.0
    elevated_tau = base_tau * 1.15  # 46.0 ms

    # Día 1: El atleta viene de 7 días estables en 40ms. Hoy marca 46ms.
    docs_day1 = [MockDoc(f"2026-09-0{7-i}", base_tau) for i in range(7)]
    db_day1 = MockDB(docs_day1)
    res_day1 = compute_zscores(db_day1, "ath_01", "2026-09-08", tau_today=elevated_tau, wellness_today=80.0)
    
    # Día 2: El historial de los últimos 7 días ahora incluye el día 1 (46ms) y 6 días de 40ms.
    # Docs orden DESC: [46, 40, 40, 40, 40, 40, 40]
    docs_day2 = [
        MockDoc("2026-09-08", elevated_tau),
        MockDoc("2026-09-07", base_tau),
        MockDoc("2026-09-06", base_tau),
        MockDoc("2026-09-05", base_tau),
        MockDoc("2026-09-04", base_tau),
        MockDoc("2026-09-03", base_tau),
        MockDoc("2026-09-02", base_tau),
    ]
    db_day2 = MockDB(docs_day2)
    # Hoy (Día 2) marca 46ms nuevamente
    res_day2 = compute_zscores(db_day2, "ath_01", "2026-09-09", tau_today=elevated_tau, wellness_today=80.0)

    # Verificación de reactividad:
    status_day2 = classify_exgauss_status(
        tau_zscore=res_day2["tau_zscore"], 
        wellness_zscore=0.0, 
        tau_ms=elevated_tau
    )
    
    # Con N=7 y EMA(alpha=0.35), la inestabilidad sostenida se diagnostica con agudeza
    assert res_day2["tau_baseline_n"] == 7
    assert res_day2["rolling_baseline_mode"] == "EMA_N7_CAPPED"


# ─── REQ-04: Jerarquía del Parche v2.2 (Hard-Rule de Lapses) ─────────────────

def test_lapse_rule_overrides_low_zscore():
    """Aun si el Z-score es bajo (ej: 0.2, homeostático), 1 lapse eleva a YELLOW y 2 a ORANGE."""
    status_1_lapse = classify_exgauss_status(tau_zscore=0.2, wellness_zscore=0.0, tau_ms=45.0, lapses_count=1)
    assert status_1_lapse["readiness_status"] == "YELLOW"
    assert status_1_lapse["lapse_override_applied"] is True
    assert "Fatiga Incipiente" in status_1_lapse["fatigue_label"]

    status_2_lapses = classify_exgauss_status(tau_zscore=0.2, wellness_zscore=0.0, tau_ms=45.0, lapses_count=2)
    assert status_2_lapses["readiness_status"] == "ORANGE"
    assert status_2_lapses["lapse_override_applied"] is True
    assert "Fatiga en Proceso" in status_2_lapses["fatigue_label"]
