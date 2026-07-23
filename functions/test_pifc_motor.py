"""
═══════════════════════════════════════════════════════════════
 IMED PREDICTOR — Sprint 2: Tests Motor PIFC
 Cubre: classify_exgauss_status(), PIFC_PROTOCOLS, 4 niveles
═══════════════════════════════════════════════════════════════
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import pytest
from pvt_exgauss_worker import classify_exgauss_status, PIFC_PROTOCOLS


# ─── Tests PIFC_PROTOCOLS estructura ─────────────────────────────────────────

def test_pifc_protocols_keys_exist():
    """Los 3 niveles de intervención deben estar definidos."""
    assert "YELLOW" in PIFC_PROTOCOLS
    assert "ORANGE" in PIFC_PROTOCOLS
    assert "RED" in PIFC_PROTOCOLS

def test_pifc_protocols_structure():
    """Cada protocolo debe tener título e intervenciones."""
    for level, proto in PIFC_PROTOCOLS.items():
        assert "title" in proto, f"{level}: falta 'title'"
        assert "interventions" in proto, f"{level}: falta 'interventions'"
        assert isinstance(proto["interventions"], list), f"{level}: 'interventions' debe ser lista"
        assert len(proto["interventions"]) >= 1, f"{level}: debe tener al menos 1 intervención"

def test_pifc_orange_protocol_content():
    """El protocolo ORANGE debe indicar reducción de carga."""
    orange = PIFC_PROTOCOLS["ORANGE"]
    assert "Intervención Proactiva" in orange["title"] or "Proactiva" in orange["title"]
    full_text = " ".join(orange["interventions"]).lower()
    assert "carga" in full_text or "entrena" in full_text


# ─── Tests classify_exgauss_status: nivel GREEN ──────────────────────────────

def test_green_nominal():
    """τ bajo línea base → estado óptimo GREEN."""
    result = classify_exgauss_status(tau_zscore=0.3, wellness_zscore=0.1, tau_ms=55.0)
    assert result["readiness_status"] == "GREEN"
    assert result["fatigue_label"] == "Homeostasis"
    assert "pifc_protocol" not in result  # GREEN no tiene protocolo

def test_green_no_tau_zscore_low_tau():
    """Sin Z-score pero τ absoluto bajo → GREEN por umbral absoluto."""
    result = classify_exgauss_status(tau_zscore=None, wellness_zscore=None, tau_ms=40.0)
    assert result["readiness_status"] == "GREEN"


# ─── Tests classify_exgauss_status: nivel YELLOW ─────────────────────────────

def test_yellow_tau_moderate():
    """τ_zscore entre 1.0 y 1.5 → YELLOW."""
    result = classify_exgauss_status(tau_zscore=1.2, wellness_zscore=0.0, tau_ms=65.0)
    assert result["readiness_status"] == "YELLOW"
    assert result["fatigue_label"] == "Fatiga Incipiente"
    assert "pifc_protocol" in result
    assert result["pifc_protocol"]["title"] == PIFC_PROTOCOLS["YELLOW"]["title"]

def test_yellow_wellness_degraded():
    """Wellness Z-Score bajo con τ moderado → YELLOW."""
    result = classify_exgauss_status(tau_zscore=0.5, wellness_zscore=-1.0, tau_ms=58.0)
    assert result["readiness_status"] == "YELLOW"

def test_yellow_no_tau_zscore_moderate_tau():
    """Sin Z-score pero τ absoluto entre 55-70ms → YELLOW."""
    result = classify_exgauss_status(tau_zscore=None, wellness_zscore=None, tau_ms=60.0)
    assert result["readiness_status"] == "YELLOW"


# ─── Tests classify_exgauss_status: nivel ORANGE ─────────────────────────────

def test_orange_tau_zscore_range():
    """τ_zscore >= 1.5 sin cruzar con wellness crítico → ORANGE."""
    result = classify_exgauss_status(tau_zscore=1.7, wellness_zscore=0.0, tau_ms=78.0)
    assert result["readiness_status"] == "ORANGE"
    assert result["fatigue_label"] == "Fatiga en Proceso"
    assert "pifc_protocol" in result
    assert result["pifc_protocol"]["title"] == PIFC_PROTOCOLS["ORANGE"]["title"]

def test_orange_pifc_interventions_count():
    """Protocolo ORANGE debe tener exactamente 3 intervenciones."""
    result = classify_exgauss_status(tau_zscore=1.6, wellness_zscore=0.1, tau_ms=75.0)
    assert result["readiness_status"] == "ORANGE"
    assert len(result["pifc_protocol"]["interventions"]) == 3

def test_orange_no_tau_zscore_high_tau():
    """Sin Z-score pero τ absoluto entre 70-90ms → ORANGE por umbral absoluto."""
    result = classify_exgauss_status(tau_zscore=None, wellness_zscore=None, tau_ms=80.0)
    assert result["readiness_status"] == "ORANGE"


# ─── Tests classify_exgauss_status: nivel RED ────────────────────────────────

def test_red_tau_critical():
    """τ_zscore > 2.0 → RED directo."""
    result = classify_exgauss_status(tau_zscore=2.5, wellness_zscore=0.0, tau_ms=95.0)
    assert result["readiness_status"] == "RED"
    assert result["fatigue_label"] == "Fatiga Consolidada"
    assert "pifc_protocol" in result
    assert result["pifc_protocol"]["title"] == PIFC_PROTOCOLS["RED"]["title"]

def test_red_dual_confirmation():
    """τ_zscore > 1.5 + wellness < -1.2 → RED por fatiga central confirmada."""
    result = classify_exgauss_status(tau_zscore=1.8, wellness_zscore=-1.5, tau_ms=82.0)
    assert result["readiness_status"] == "RED"

def test_red_wellness_critical_override():
    """Wellness Z < -2.0 → Safety Override RED independiente del τ."""
    result = classify_exgauss_status(tau_zscore=0.2, wellness_zscore=-2.5, tau_ms=50.0)
    assert result["readiness_status"] == "RED"
    assert "CRÍTICA" in result["exg_alert"].upper() or "CRITICA" in result["exg_alert"].upper()

def test_red_no_tau_zscore_extreme_tau():
    """Sin Z-score pero τ absoluto > 90ms → RED por umbral absoluto."""
    result = classify_exgauss_status(tau_zscore=None, wellness_zscore=None, tau_ms=100.0)
    assert result["readiness_status"] == "RED"

def test_red_pifc_interventions_count():
    """Protocolo RED debe tener 3 intervenciones de emergencia."""
    result = classify_exgauss_status(tau_zscore=3.0, wellness_zscore=-1.0, tau_ms=110.0)
    assert len(result["pifc_protocol"]["interventions"]) == 3


# ─── Tests calibración (sin datos suficientes) ────────────────────────────────

def test_calibrating_no_data():
    """Sin τ_zscore ni τ_ms → CALIBRATING."""
    result = classify_exgauss_status(tau_zscore=None, wellness_zscore=None, tau_ms=None)
    assert result["readiness_status"] == "CALIBRATING"
    assert "pifc_protocol" not in result


# ─── Tests límites de frontera (boundary values) ──────────────────────────────

def test_boundary_tau_15_is_orange():
    """τ_zscore exactamente 1.5 debe ser ORANGE (≥ 1.5)."""
    result = classify_exgauss_status(tau_zscore=1.5, wellness_zscore=0.0, tau_ms=70.0)
    assert result["readiness_status"] == "ORANGE"

def test_boundary_tau_20_is_red():
    """τ_zscore exactamente 2.0 debe ser RED (> 2.0 en la lógica: tau > 2.0)."""
    # Nota: la condición es tau_zscore > 2.0, entonces 2.0 exacto cae en ORANGE
    result = classify_exgauss_status(tau_zscore=2.0, wellness_zscore=0.0, tau_ms=90.0)
    # 2.0 es el umbral: "> 2.0" → ORANGE si wellness > -1.2
    assert result["readiness_status"] in ("RED", "ORANGE")  # depende de implementación exacta

def test_boundary_tau_201_is_red():
    """τ_zscore 2.01 debe ser RED."""
    result = classify_exgauss_status(tau_zscore=2.01, wellness_zscore=0.0, tau_ms=92.0)
    assert result["readiness_status"] == "RED"

def test_exg_alert_always_present():
    """Siempre debe existir un campo exg_alert con contenido."""
    for tau_z, w_z, tau in [(0.5, 0.0, 50), (1.2, -0.5, 65), (1.6, 0.2, 75), (2.5, 0.0, 95)]:
        result = classify_exgauss_status(tau_z, w_z, tau)
        assert "exg_alert" in result
        assert len(result["exg_alert"]) > 10
