import numpy as np
from scipy.stats import exponnorm
from scipy.optimize import minimize

def fit_exgaussian_robust(trials: list[float]) -> dict | None:
    # 1. Filtro estático
    trials_arr = np.array([t for t in trials if 120 <= t <= 1000], dtype=float)
    n = len(trials_arr)
    if n < 20:
        return None

    # 2. Inicialización por Método de Momentos (MM) para estabilidad
    mean_val = np.mean(trials_arr)
    var_val = np.var(trials_arr, ddof=1)
    
    # Tercer momento central
    m3 = np.mean((trials_arr - mean_val)**3)
    
    # Estimación de Tau inicial
    if m3 > 0:
        tau_init = (m3 / 2.0)**(1/3)
    else:
        tau_init = 0.2 * np.sqrt(var_val)
        
    # Limitar tau inicial para evitar valores imaginarios o ilógicos
    tau_init = min(tau_init, np.sqrt(var_val) * 0.9)
    
    sigma_init = np.sqrt(max(1.0, var_val - tau_init**2))
    mu_init = mean_val - tau_init
    
    # Asegurar que los valores iniciales estén dentro de límites fisiológicos razonables
    mu_init = np.clip(mu_init, 100.0, 400.0)
    sigma_init = np.clip(sigma_init, 5.0, 200.0)
    tau_init = np.clip(tau_init, 10.0, 300.0)

    # 3. Optimización por MLE acotada (L-BFGS-B)
    # Definimos la función de menos log-verosimilitud (Negative Log-Likelihood)
    # exponnorm de scipy está parametrizado con:
    # K = tau / sigma, loc = mu, scale = sigma
    def neg_log_likelihood(params):
        mu, sigma, tau = params
        K = tau / sigma
        # Calcular logpdf
        log_pdf = exponnorm.logpdf(trials_arr, K, loc=mu, scale=sigma)
        nll = -np.sum(log_pdf)
        if np.isnan(nll) or np.isinf(nll):
            return 1e10
        
        # Penalización/Regularización L2 para evitar colapsos en muestras pequeñas
        # Penaliza desviaciones extremas de valores típicos
        # Mu típico: 200, Sigma típico: 40, Tau típico: 60
        mu_penalty = 0.001 * (mu - 220)**2
        sigma_penalty = 0.01 * (sigma - 45)**2
        tau_penalty = 0.005 * (tau - 65)**2
        
        return nll + mu_penalty + sigma_penalty + tau_penalty

    # Límites estrictos para evitar divergencia de MLE con N=30
    bounds = [
        (100.0, 450.0),  # mu bounds
        (10.0, 250.0),   # sigma bounds
        (10.0, 350.0)    # tau bounds
    ]

    try:
        res = minimize(
            neg_log_likelihood, 
            x0=[mu_init, sigma_init, tau_init], 
            method='L-BFGS-B', 
            bounds=bounds,
            options={'ftol': 1e-6}
        )
        
        if not res.success:
            # Si la optimización acotada falla, usamos scipy fit estándar como fallback secundario
            K, loc, scale = exponnorm.fit(trials_arr)
            mu, sigma, tau = loc, scale, K * scale
        else:
            mu, sigma, tau = res.x

        exg_mean = mu + tau
        exg_var = sigma**2 + tau**2
        
        # Re-calcular log-verosimilitud
        log_lik = float(np.sum(exponnorm.logpdf(trials_arr, tau/sigma, loc=mu, scale=sigma)))

        if not (100 <= mu <= 450) or sigma <= 0 or tau <= 0:
            return None

        return {
            "mu_ms": round(mu, 2),
            "sigma_ms": round(sigma, 2),
            "tau_ms": round(tau, 2),
            "exg_mean_ms": round(exg_mean, 2),
            "n_trials": int(n),
            "log_lik": round(log_lik, 3),
            "method": "bounded_mle_penalized"
        }
    except Exception as e:
        print(f"Error optimizando: {e}")
        return None

# Generar datos de prueba cortos (30 ensayos) con un outlier alto
np.random.seed(42)
# Generar distribución ex-gaussiana real: mu=200, sigma=30, tau=80
raw_data = np.random.normal(200, 30, 25) + np.random.exponential(80, 25)
# Añadir outliers
raw_data = np.append(raw_data, [950.0, 110.0, 150.0, 220.0, 210.0]) # 30 trials en total

print("Datos generados:", len(raw_data))
result_robust = fit_exgaussian_robust(raw_data)
print("Resultado robusto:", result_robust)

# Comparar con scipy fit directo
trials_clean = np.array([t for t in raw_data if 120 <= t <= 1000])
K, loc, scale = exponnorm.fit(trials_clean)
print("Resultado original (scipy fit):")
print(f"mu: {loc:.2f}, sigma: {scale:.2f}, tau: {K*scale:.2f}")
