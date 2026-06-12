import sys
import os
import numpy as np
from unittest.mock import Mock, patch

# Agregamos la carpeta functions al path para poder importar pvt_exgauss_worker
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions'))
import pvt_exgauss_worker as worker

print("=== VERIFICACION DE ROBUSTEZ EX-GAUSSIANO ===")

# Prueba 1: Estabilidad de MLE con ruido atípico
print("\n[1] Probando fit_exgaussian con N=30 y ruido atipico")
np.random.seed(42)
raw_data = np.random.normal(200, 30, 25) + np.random.exponential(80, 25)
raw_data = np.append(raw_data, [950.0, 110.0, 150.0, 220.0, 210.0])

res = worker.fit_exgaussian(raw_data)
if res:
    print(f"Resultado robusto: tau_ms={res['tau_ms']}, sigma_ms={res['sigma_ms']}, mu_ms={res['mu_ms']}")
    assert res['tau_ms'] < 100, "Tau deberia estar estabilizado por debajo de 100 (ground truth 80)"
    print("[OK] Ajuste robusto validado con exito.")
else:
    print("[ERROR] fit devolvio None")

# Prueba 2: Lógica Semáforo (Override de Wellness)
print("\n[2] Probando Semaforo (classify_exgauss_status)")
status_red = worker.classify_exgauss_status(tau_zscore=-0.5, wellness_zscore=-2.5, tau_ms=200)
print(f"Estado con Wellness critico (-2.5) y Tau rapido (-0.5): {status_red['readiness_status']}")
assert status_red['readiness_status'] == 'RED', "El status debe ser RED debido a wellness critico."
print("[OK] Override de Wellness Critico funciona correctamente.")

status_yellow = worker.classify_exgauss_status(tau_zscore=-0.5, wellness_zscore=-1.5, tau_ms=200)
print(f"Estado con Wellness moderado (-1.5) y Tau rapido (-0.5): {status_yellow['readiness_status']}")
assert status_yellow['readiness_status'] == 'YELLOW', "Debe ser YELLOW porque no supera limite RED de -2.0 ni es Tau elevado."
print("[OK] Regla amarilla normal funciona.")

status_fallback_red = worker.classify_exgauss_status(tau_zscore=None, wellness_zscore=None, tau_ms=90)
print(f"Estado fallback con Tau 90ms: {status_fallback_red['readiness_status']}")
assert status_fallback_red['readiness_status'] == 'RED', "Fallback debe alertar RED sobre 80ms."

print("\n=== VERIFICACION EXITOSA ===")
