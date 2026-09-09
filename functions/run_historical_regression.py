"""
══════════════════════════════════════════════════════════════════════════════
 IMED PREDICTOR — Script de Regresión Histórica (Test 2)
 Compara Z-Score Antiguo (N=15 + SMA) vs. Nuevo (N=7 + EMA + Cap) sobre la
 base de datos real de Firestore (Daily_Performance) y exporta el CSV oficial.
══════════════════════════════════════════════════════════════════════════════
"""
import os
import sys
import math
import csv
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Configurar path para importar pvt_exgauss_worker
functions_dir = os.path.dirname(__file__)
sys.path.insert(0, functions_dir)

import firebase_admin
from firebase_admin import credentials, firestore

from pvt_exgauss_worker import (
    classify_exgauss_status,
    EMA_ALPHA,
    SIGMA_CAP_MAX,
    SIGMA_FLOOR_MIN
)

# ── 1. Inicializar Firebase ──────────────────────────────────────────────────
sa_path = os.path.join(functions_dir, "serviceAccount.json")
cred = credentials.Certificate(sa_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

print("🔥 Conectado exitosamente a Firestore (app-imed-sport)")

# ── 2. Algoritmo Antiguo (N=15 + SMA, sin Cap de Sigma) ─────────────────────
def compute_old_zscore(tau_history_all, tau_today):
    """Calcula Z-score según la lógica antigua (N=15, SMA, sin cap)."""
    # Ventana de 15 sesiones previas
    tau_hist_15 = tau_history_all[:15]
    n = len(tau_hist_15)
    if n < 5 or tau_today is None:
        return None, None, n, "INSUFFICIENT_DENSITY"
    
    mean_old = float(np.mean(tau_hist_15))
    sample_var = float(np.var(tau_hist_15, ddof=1)) if n > 1 else 0.0
    prior_var = 15.0 ** 2
    prior_n = 5
    posterior_var = ((n - 1) * sample_var + prior_n * prior_var) / ((n - 1) + prior_n)
    sd_old = max(math.sqrt(posterior_var), 5.0)
    
    z_old = round((tau_today - mean_old) / sd_old, 3)
    return z_old, round(mean_old, 2), round(sd_old, 2), "N15_SMA"

# ── 3. Algoritmo Nuevo v3.3 (N=7 + EMA(0.35) + Cap 18.84ms) ────────────────
def compute_new_zscore(tau_history_all, tau_today):
    """Calcula Z-score según la lógica nueva v3.3 (N=7, EMA con alpha=0.35, Cap 18.84ms)."""
    tau_hist_7 = tau_history_all[:7]
    n = len(tau_hist_7)
    if n < 3 or tau_today is None:
        return None, None, n, False, "CALIBRATING"
    
    sigma_capped = False
    if n >= 7:
        chrono = tau_hist_7[::-1]
        ema = chrono[0]
        for t in chrono[1:]:
            ema = (t * EMA_ALPHA) + (ema * (1.0 - EMA_ALPHA))
        mean_new = ema
        mode = "EMA_N7_CAPPED"
    else:
        mean_new = float(np.mean(tau_hist_7))
        mode = "SMA_PROVISIONAL"
    
    sample_var = float(np.var(tau_hist_7, ddof=1)) if n > 1 else 0.0
    prior_var = 15.0 ** 2
    prior_n = 3
    posterior_var = ((n - 1) * sample_var + prior_n * prior_var) / ((n - 1) + prior_n)
    sd_new = math.sqrt(posterior_var)
    
    if sd_new > SIGMA_CAP_MAX:
        sd_new = SIGMA_CAP_MAX
        sigma_capped = True
    sd_new = max(sd_new, SIGMA_FLOOR_MIN)
    
    z_new = round((tau_today - mean_new) / sd_new, 3)
    return z_new, round(mean_new, 2), round(sd_new, 2), sigma_capped, mode

# ── 4. Descargar y agrupar todas las evaluaciones por atleta ─────────────────
print("📥 Descargando registros de Daily_Performance...")
all_docs = list(db.collection("Daily_Performance").order_by("date").stream())
print(f"✅ Total registros recuperados: {len(all_docs)}")

# Organizar por atleta y fecha
records_by_athlete = {}
for doc in all_docs:
    d = doc.to_dict()
    aid = d.get("athleteId") or "UNKNOWN"
    if aid not in records_by_athlete:
        records_by_athlete[aid] = []
    records_by_athlete[aid].append((doc.id, d))

# ── 5. Procesar Regresión Histórica ──────────────────────────────────────────
rows_out = []
updates_count = 0
status_shifts = {}
capped_count = 0

for aid, athlete_records in records_by_athlete.items():
    # Ordenar cronológicamente ascendente por fecha
    athlete_records.sort(key=lambda x: x[1].get("date", ""))
    
    history_taus = []  # acumulará taus anteriores
    
    for doc_id, data in athlete_records:
        date_str = data.get("date", "")
        ath_name = data.get("athleteName", aid)
        aa = data.get("advanced_analysis", {})
        tau_today = aa.get("tau_ms")
        wellness_z = aa.get("wellness_zscore")
        lapses = aa.get("lapses") or data.get("lapses") or 0
        
        # Calcular con histórico hasta antes de esta fecha (invertido a orden DESC)
        tau_hist_desc = history_taus[::-1]
        
        z_old, mean_old, sd_old, mode_old = compute_old_zscore(tau_hist_desc, tau_today)
        z_new, mean_new, sd_new, capped_new, mode_new = compute_new_zscore(tau_hist_desc, tau_today)
        
        if capped_new:
            capped_count += 1
            
        status_old_dict = classify_exgauss_status(z_old, wellness_z, tau_today, lapses)
        status_new_dict = classify_exgauss_status(z_new, wellness_z, tau_today, lapses)
        
        st_old = status_old_dict.get("readiness_status", "GREEN")
        st_new = status_new_dict.get("readiness_status", "GREEN")
        
        delta_z = round(z_new - z_old, 3) if (z_new is not None and z_old is not None) else None
        
        shift_key = f"{st_old} -> {st_new}"
        status_shifts[shift_key] = status_shifts.get(shift_key, 0) + 1
        
        row = {
            "doc_id": doc_id,
            "athlete_id": aid,
            "athlete_name": ath_name,
            "date": date_str,
            "tau_today_ms": tau_today,
            "lapses": lapses,
            "tau_history_n": len(tau_hist_desc),
            "old_baseline_mean": mean_old,
            "old_baseline_sd": sd_old,
            "old_zscore": z_old,
            "old_status": st_old,
            "new_mode": mode_new,
            "new_baseline_mean": mean_new,
            "new_baseline_sd": sd_new,
            "new_sigma_capped": capped_new,
            "new_zscore": z_new,
            "new_status": st_new,
            "delta_z": delta_z,
            "status_changed": (st_old != st_new)
        }
        rows_out.append(row)
        
        # Actualizar en Firestore si hay cambio de valores
        if tau_today is not None and z_new is not None:
            try:
                db.collection("Daily_Performance").document(doc_id).set({
                    "advanced_analysis": {
                        "tau_zscore": z_new,
                        "tau_baseline_mean_ms": mean_new,
                        "tau_baseline_sd_ms": sd_new,
                        "tau_baseline_sigma_capped": capped_new,
                        "rolling_baseline_mode": mode_new,
                        "rolling_baseline_n_requested": 7,
                        "rolling_baseline_min_required": 3,
                        "rolling_baseline_alpha": EMA_ALPHA if mode_new == "EMA_N7_CAPPED" else None,
                        "rolling_baseline_sigma_cap": SIGMA_CAP_MAX,
                        "readiness_status": st_new,
                        "fatigue_label": status_new_dict.get("fatigue_label"),
                        "exg_alert": status_new_dict.get("exg_alert"),
                        "version": "exgauss-3.3"
                    }
                }, merge=True)
                updates_count += 1
            except Exception as e:
                print(f"Error actualizando {doc_id}: {e}")
        
        # Agregar el tau de hoy al historial para las siguientes fechas
        if tau_today is not None:
            history_taus.append(tau_today)

# ── 6. Exportar Archivo CSV ──────────────────────────────────────────────────
csv_filename = os.path.join(os.path.dirname(functions_dir), "regresion_historica_zscore_n7_ema.csv")
with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows_out[0].keys())
    writer.writeheader()
    writer.writerows(rows_out)

print(f"\n📊 ═══════════════════════════════════════════════════════════════")
print(f"  REGRESIÓN HISTÓRICA COMPLETADA EXITOSAMENTE")
print(f"  Archivo generado: {csv_filename}")
print(f"  Total registros evaluados: {len(rows_out)}")
print(f"  Documentos actualizados en Firestore: {updates_count}")
print(f"  Registros con Sigma Capped (Clamping en 18.84ms): {capped_count}")
print(f"\n  Distribución de Transiciones de Estado (Antiguo -> Nuevo):")
for shift, count in sorted(status_shifts.items(), key=lambda x: -x[1]):
    print(f"    • {shift}: {count} casos")
print(f"═══════════════════════════════════════════════════════════════\n")
