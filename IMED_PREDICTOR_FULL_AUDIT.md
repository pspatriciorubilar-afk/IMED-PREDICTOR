# Auditoría Integral: Ecosistema IMED Predictor

**Fecha:** 12 de Junio de 2026  
**Versión General:** IMED Sport 4.x / Motor Inteligencia 3.0  
**Enfoque:** Auditoría exhaustiva de arquitectura de software, aplicación móvil, backend, algoritmos y estado de desarrollo.

---

## 1. Resumen Ejecutivo
IMED Predictor es una plataforma clínica de telemetría y prevención de lesiones para deportistas de élite. El sistema conecta la carga interna (fatiga del Sistema Nervioso Central mediante PVT y Wellness) con la carga externa (desgaste mecánico vía GPS). El proyecto ha evolucionado hacia una infraestructura robusta orientada a eventos (*Serverless*), eliminando servidores convencionales y garantizando un escalado seguro y cálculo en tiempo real.

---

## 2. Arquitectura de Software

La arquitectura se divide en tres bloques fuertemente desacoplados, comunicados a través de Firestore en Google Cloud.

### 2.1. Aplicación Móvil (Athlete HUD)
- **Tecnología:** Flutter SDK (Dart) versión >=3.0.0.
- **Gestión de Estado:** `flutter_riverpod` (v2.5.1).
- **Almacenamiento Local (Offline-First):** Bases de datos ultra-rápidas `isar` e `hive` para persistencia en modo competencia/sin red.
- **Biometría:** Captura de variabilidad de frecuencia cardíaca (HRV) usando cámara (`camera` API) y algoritmos fotopletismográficos (PPG).
- **Sincronización:** Tareas en segundo plano con `workmanager`.
- **UI/UX:** Diseño premium (Dark Mode HUD), notificaciones circadianas, gráficas de tendencias (`fl_chart`).
- **Capacidades:** Permite realizar el Test PVT (Psychomotor Vigilance Task), registrar *Wellness* (bienestar subjetivo) y recopilar biometría.

### 2.2. Panel de Control (Dashboard)
Existen dos ecosistemas de dashboard coexistentes/transicionales:
1. **Dashboard Flutter:** Ubicado en `/dashboard`, utiliza Flutter web, Riverpod, y `fl_chart`.
2. **Web Vanilla SaaS (`live_app.js`):** Interfaz clínica con estilo *Glassmorphism*, inmersiva y reactiva, construida con JS/HTML5 y Firebase SDK.
- **Funcionalidad:** Mapeo en vivo de *Daily Performance*, gráficas de dispersión de correlación (IRI vs Desaceleraciones) con Chart.js y subida de archivos CSV (GPS).

### 2.3. Backend Serverless (Motor de Inteligencia)
- **Tecnología:** Google Cloud Functions (2da Gen) en Python 3.13.
- **Arquitectura:** 100% *Event-Driven*. No hay tareas programadas (Cron jobs); se activa mediante *triggers* de Firestore (`@firestore_fn.on_document_created`) y endpoints HTTP (`@https_fn.on_call`).
- **Core Clínico:** `scipy` (optimización L-BFGS-B), `pandas` (normalización), `numpy`.
- **Seguridad y Rendimiento:** Se emplean importaciones diferidas para mitigar los tiempos de *Cold Start*. El *know-how* algorítmico queda oculto del frontend.

---

## 3. Estado de Desarrollo y Bases de Datos

### Estado Actual: *Enterprise-Level SaaS* (Nivel 3 Analytics Ready)
El ecosistema ha madurado significativamente, migrando de arquitecturas monolíticas (Express/Node.js/MySQL) a ecosistemas 100% Serverless con Cloud Functions y Firestore.  
Las métricas operan ahora de manera autónoma, logrando un estado de madurez robusto: es resistente a fallos de muestra, autoadaptativo (baseline dinámica) e incluye *Safety Overrides*.

### Base de Datos y Flujo (Firestore)
- **Capa Inmutable (`athletes/{id}/measurements`):** Almacena datos crudos provenientes de la app. Es un registro protegido, ideal para auditorías.
- **Capa Analítica (`Daily_Performance`):** Almacena resúmenes y proyecciones (Z-Scores, GPS integrados, cruces de carga y motor de decisiones). Opera bajo el principio matemático de Idempotencia para evitar duplicidades.

---

## 4. Algoritmos y Métricas Clínicas

El sistema destaca por la complejidad e innovación de sus algoritmos neuromecánicos:

### 4.1. Motor Ex-Gaussiano (Test PVT)
- **Objetivo:** Filtrar ruido en los tiempos de reacción del atleta para obtener una lectura clínica de la fatiga psicomotora pura.
- **Avance Matemático:** Utiliza estabilización MLE acotada (Método de Momentos + L-BFGS-B + Regularización L2). 
- **Fiabilidad:** Consigue converger en mediciones exactas del parámetro *Tau* ($\tau$) incluso frente a "ruido" o errores humanos durante las pruebas (30 ensayos por test).
- **Control de Varianza:** Exige al menos 8 sesiones de historial (en 21 días) y aplica límites estadísticos para evitar caídas artificiales en la línea base (Baseline).

### 4.2. Índice de Vulnerabilidad Neuro-Mecánica (IVN)
Fórmula central del sistema que cruza carga externa (mecánica) y carga interna (neurológica).
- **IRI (Índice de Recuperación Integral):** Valor 0-100 obtenido del sistema nervioso (latencia, lapsos y Ex-Gauss).
- **ACWR (Acute:Chronic Workload Ratio):** Relación de carga aguda (7 días) frente a crónica (28 días) proveniente del GPS.
- **Carga Mecánica (GPS):** Normaliza e integra variables críticas como Desaceleraciones Altas (Z5) y Distancias de Sprint. El motor detecta semánticamente las columnas CSV sin importar la marca de GPS (Catapult, Wimu, StatSports, etc.).
- **Evaluación Final:** El IVN calcula un score de riesgo y cataloga al deportista en `VERDE`, `AMARILLO`, o `ROJO`, entregando sugerencias tácticas.

### 4.3. Protocolo *Safety Override* (Cinturón de Seguridad)
- Sobrescribe la evaluación matemática si existen banderas rojas.
- **Wellness Red-Alert:** Si el bienestar subjetivo (encuesta) cae críticamente por debajo de -2.0 en su *Z-Score*, el semáforo se fuerza a **ROJO** (Riesgo Crítico de Sobreentrenamiento) independientemente de si los reflejos motores se ven bien.
- **Lapsos PVT:** Si el deportista acumula más de 2 lapsos (fallas completas de atención) se dispara una advertencia de riesgo de coordinación.

---

## 5. Capacidades y Features Clave

1. **Adaptador Universal Inteligente de GPS:** El backend en Python ingesta archivos CSV y utiliza detección semántica y *scoring* de palabras para mapear de forma inteligente métricas como *Sprint*, *Desaceleración Máxima*, sin requerir formato estricto.
2. **Offline-First Clínico:** El atleta puede realizar pruebas PVT en aviones o sin internet; la app almacena localmente (Isar/Hive) y sincroniza al detectar conexión.
3. **Re-calibración Dinámica (Fase de Choque):** La línea base de métricas de los deportistas se ajusta dinámicamente utilizando sus últimos históricos, entendiendo los momentos de carga y descarga de la temporada.
4. **Resiliencia Cloud:** Capacidad para atender múltiples deportistas sincronizando simultáneamente después de los entrenamientos gracias al uso concurrente de Google Cloud Functions.

## 6. Conclusión
El Sistema **IMED Predictor** posee componentes algorítmicos comparables a sistemas élite de alto presupuesto deportivo. El desarrollo muestra una arquitectura moderna en la nube con Flutter, asegurando rendimiento y un marco matemático y estadístico (Ex-Gauss) excepcionalmente robusto, blindado para la prevención en el alto rendimiento.
