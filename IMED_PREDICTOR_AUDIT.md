# Auditoría Técnica y Funcional: Sistema IMED Predictor

**Fecha:** 9 de Mayo de 2026  
**Versión:** 2.0 (Producción)  
**Proyecto:** SaaS de Prevención de Lesiones — Ecosistema IMED Sport

---

## 1. Resumen Ejecutivo
IMED Predictor es una plataforma de inteligencia deportiva de élite diseñada para cerrar la brecha entre la carga interna (fatiga del sistema nervioso central) y la carga externa (estrés mecánico). El sistema consolida datos de la aplicación móvil IMED Sport con archivos GPS externos para predecir el riesgo de lesiones mediante el algoritmo propietario **IVN (Índice de Vulnerabilidad Neuro-Mecánica)**.

---

## 2. Arquitectura de Software

### 2.1. Frontend (Dashboard)
- **Tecnología:** HTML5 / CSS3 (Vanilla) / JS (v9 Compat SDK).
- **Diseño:** Estética *Glassmorphism* (Elite Dark Mode) optimizada para visualización clínica y rendimiento.
- **Visualización:** Integración con **Chart.js** para gráficos de correlación dinámicos y scatter plots.
- **Conectividad:** Firebase JS SDK con listeners en tiempo real para actualizaciones sin recarga de página.

### 2.2. Backend (Motor de Inteligencia)
- **Tecnología:** Google Cloud Functions (2da Gen) sobre Python 3.13.
- **Arquitectura:** Función Callable de baja latencia con importaciones diferidas para optimizar el tiempo de respuesta (cold start).
- **Librerías Core:** `pandas` para normalización de datos GPS, `firebase-admin` para orquestación de bases de datos.

### 2.3. Base de Datos (Firestore)
- **Colección `athletes/` (Inmutable):** Contenedor de datos maestros. Solo lectura para el Dashboard, garantizando que el uso del SaaS no altere la experiencia del atleta en la app móvil.
- **Colección `Daily_Performance/` (Maestra):** Punto de consolidación de cada sesión. Almacena el cruce de IRI, Lapses, métricas GPS y el diagnóstico final del motor.

---

## 3. El Algoritmo IVN v2.0 (Cerebro del Sistema)
El sistema ha sido actualizado bajo la lógica de "Neuro-Mecánica de Alta Intensidad", implementando el cálculo de carga aguda/crónica.

### 3.1. Dimensiones de Análisis
1.  **IRI (Índice de Recuperación Integral):** Evaluado en una escala 0-100. Refleja la disponibilidad biológica del atleta.
2.  **ACWR (Acute:Chronic Workload Ratio):** Ratio de carga de 7 días (aguda) vs 28 días (crónica). Un ratio > 1.5 activa alertas de fatiga acumulada.
3.  **Carga Mecánica Z5:** Análisis de desaceleraciones de alta intensidad (>3m/s²).

### 3.2. Fórmula Matemática
$$IVN = \frac{ACWR_{GPS} \times \text{Desaceleraciones } Z_5}{IRI_{IMED\_SNC} / 100}$$

### 3.3. Clasificación de Riesgo y Prescripción
- **🔴 RIESGO CRÍTICO (Red):** IRI < 60 + Carga Mecánica > 15.
  - *Prescripción:* **Optimizar** carga. Reducción inmediata de volumen e intensidad mecánica.
- **🟡 RIESGO COORDINACIÓN (Yellow):** Lapses > 2.
  - *Prescripción:* **Reprogramar** tareas de alta precisión neuro-motora. Priorizar recuperación activa.
- **🟡 RIESGO DE CARGA (Yellow):** ACWR > 1.5.
  - *Prescripción:* **Monitorear** progresión. El atleta ha excedido su capacidad de carga histórica.
- **🟢 ADAPTACIÓN ÓPTIMA (Green):** IRI > 85 + ACWR Estable.
  - *Prescripción:* **Mantener** planificación actual.

---

## 4. Auditoría de Flujo de Datos

1.  **Ingesta:** Carga manual de CSVs agnósticos (Oliver, UC-CENDIA, etc.).
2.  **Persistencia:** Almacenamiento automático en `Storage/gps/` para auditoría forense posterior.
3.  **Procesamiento:** El Motor IVN en la nube normaliza las columnas del CSV (mapeo agnóstico) y extrae los datos neuro del atleta en Firestore.
4.  **Entrega:** El resultado se renderiza en el Dashboard en < 3 segundos.

---

## 5. Seguridad y Cumplimiento
- **IAM:** Separación de roles. El sistema utiliza el plan Blaze para gestionar las APIs de Cloud Build y Cloud Functions.
- **Security Rules:** Reglas de Firestore implementadas para permitir la coexistencia de dashboards heredados sin comprometer la integridad de la base de datos central.
- **Escalabilidad:** Gracias al entorno de Google Cloud, el sistema soporta el análisis simultáneo de miles de atletas sin degradación de rendimiento.

---

## 6. Conclusión de Auditoría
El sistema cumple con los estándares de **SaaS Médico-Deportivo**. La separación entre el registro de datos y el motor de análisis permite que la propiedad intelectual (el algoritmo) esté protegida y sea fácilmente actualizable sin tocar la interfaz de usuario.

---
*Fin del Informe de Auditoría*
