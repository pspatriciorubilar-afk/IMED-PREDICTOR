# Algoritmo de Decisión Clínica: Z-Scores (HRV vs PVT)

Este documento detalla la lógica matemática alojada en el backend para generar el "Readiness Score" del atleta basándose en la variabilidad de su propia frecuencia cardíaca y fatiga central.

## 1. La Línea Base (Calibración)
Durante los primeros 7 días, el algoritmo recopila datos. Al alcanzar 7 registros, calcula:
- **$\mu$ (Media)** y **$\sigma$ (Desviación Estándar)** de ambas métricas: `hrvLnRMSSD` y `pvtMeanLatency`.

## 2. El Z-Score (Día 8+)
El Z-Score nos dice cuántas desviaciones estándar ($\sigma$) se aleja el valor actual de la norma individual del atleta.
Fórmula: $Z = (X - \mu) / \sigma$

## 3. Matriz de Ponderación (Semáforo)
El cerebro estadístico cruza los Z-Scores para dictaminar el estado:

1. **Estado ROJO (Alerta Crítica)**
   - Condición: $Z_{HRV} < -1.5$ **O** $Z_{PVT} > 2$
   - Significado: Caída brusca de la recuperación autonómica o lentitud neuronal extrema.
   - Ponderación: El Score cae automáticamente por debajo de 30.

2. **Estado AMARILLO (Precaución)**
   - Condición: $Z_{HRV}$ entre $-1.5$ y $-1.0$ **O** $Z_{PVT} > 1$
   - Significado: Fatiga moderada. Se recomienda bajar la carga de impacto.
   - Ponderación: El Score se sitúa entre 40 y 65, dependiendo exacto de $Z$.

3. **Estado VERDE (Óptimo)**
   - Condición: $Z_{HRV} > -1.0$ **Y** $Z_{PVT} \le 1$
   - Significado: Listo para entrenamientos hipertróficos o técnicos de alta competencia.
   - Ponderación: El Score base es 90, subiendo hasta 100 con mejores HRV.

*Si el atleta reporta `sleep_hours < 6` (vía Wellness Survey), una etiqueta penalizadora adjunta contextúa la caída del Z-Score.*
