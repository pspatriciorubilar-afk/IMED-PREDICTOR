# 🧠 Especificaciones Técnicas: IMED Sport SNC Engine (v4.0)
**Documentación técnica sobre el algoritmo de puntuación neuro-cognitiva y el Índice de Recuperación Integral (IRI).**

---

## 1. Fundamento Científico: Test PVT
El motor de IMED Sport se basa en la **Tarea de Vigilancia Psicomotora (PVT)**, validada por más de 20 años de investigación como el *Gold Standard* para medir la fatiga del Sistema Nervioso Central.

### ¿Qué medimos realmente?
A diferencia de los tests de reacción simples, el PVT mide la **estabilidad de la atención sostenida**. No buscamos solo la respuesta más rápida, sino la consistencia del SNC bajo demanda.

---

## 2. Métricas Críticas de Entrada
El algoritmo captura y procesa múltiples variables de cada sesión de 2 minutos:

*   **Latencia Media (RMs):** La velocidad base de procesamiento sináptico.
*   **Lapsos de Atención (Lapses):** Cualquier respuesta superior a **500ms**. Es la métrica más sensible a la falta de sueño y la fatiga acumulada.
*   **Rango de Variabilidad:** Diferencia entre el 10% de respuestas más rápidas y el 10% más lentas. Un rango amplio indica inestabilidad neuro-cognitiva.

---

## 3. La "Media de Oro" (Baseline Dinámico)
El SNC Engine no utiliza promedios poblacionales. Cada deportista es comparado contra su propio **Perfil de Máximo Rendimiento**.

1.  **Normalización:** El sistema establece una "Media de Oro" tras las primeras 7 mediciones.
2.  **Desviación Estándar:** El algoritmo calcula qué tan lejos está el deportista de su estado óptimo hoy.
3.  **Z-Score Adaptativo:** Las puntuaciones se ajustan diariamente según la tendencia de los últimos 15 días.

---

## 4. El Índice de Recuperación Integral (IRI)
El IRI es el resultado de una **fusión lógica ponderada** que integra la biología (PVT) con la percepción (Wellness).

### Algoritmo de Ponderación:
`IRI = (Puntuación_PVT * 0.70) + (Puntuación_Wellness * 0.30)`

*   **Penalización por Lapsos:** Cada lapso detectado reduce el IRI de forma exponencial (un solo lapso puede bajar la puntuación en 15-20 puntos).
*   **Detección de "Rendimiento Forzado":** Si la latencia es buena pero el Wellness es bajo (pobre sueño/alto estrés), el algoritmo aplica un factor de corrección de **-15%**. Esto indica que el atleta está rindiendo por "voluntad", pero su reserva biológica está en riesgo.

---

## 5. Clasificación de Estados
El resultado final sitúa al deportista en una zona de acción específica:

| Puntuación | Estado | Significado para el Entrenador |
| :--- | :--- | :--- |
| **85 - 100** | **READY (Óptimo)** | Apto para cargas máximas de intensidad y volumen. |
| **70 - 84** | **CAUTION (Precaución)** | Fatiga leve. Se recomienda monitoreo o ajustes moderados. |
| **50 - 69** | **FATIGUE (Fatiga)** | Riesgo de lesión aumentado. Reducir carga cognitiva y física. |
| **< 50** | **EXHAUSTED (Agotado)** | Riesgo crítico. Priorizar recuperación total o descanso activo. |

---

## 6. Validaciones Globales
El algoritmo de IMED Sport replica los estándares utilizados por:
*   **NASA:** Para el monitoreo de astronautas en misiones de larga duración.
*   **Fuerzas Especiales:** Para evaluar la capacidad de toma de decisiones bajo estrés extremo.
*   **Élite Deportiva:** Utilizado en las ligas más importantes del mundo (NFL, NBA, Premier League) para la gestión de carga.

---
*Documentación Confidencial - IMED Sport v4.11 - 2026*
