# Plan de Implementación: IMED Predictor SaaS

Este documento detalla la arquitectura y el flujo de trabajo para el sistema de prevención de lesiones de élite.

## 1. Arquitectura de Datos

### Colecciones Firestore
- **athletes (Solo Lectura)**: `athletes/{athleteId}/measurements/{measurementId}`
- **Daily_Performance (Nueva)**: `Daily_Performance/{athleteId}_{date}`
    - Campos: `iri`, `lapses`, `latency`, `accel_high`, `decel_high`, `max_speed`, `sprint_distance`, `ivn_score`, `risk_level`, `timestamp`.

## 2. Motor de Inteligencia (Cloud Function - Python)
- **Trigger**: `google.storage.object.finalize` en el bucket de GPS.
- **Procesamiento**:
    1. Parseo de CSV (Agnóstico: mapeo de columnas clave).
    2. Consulta de última evaluación en `athletes/`.
    3. Cálculo de **IVN** (Índice de Vulnerabilidad Neuro-Mecánica).
    4. Persistencia en `Daily_Performance`.

## 3. Dashboard Web (Flutter)
- **Estética**: Dark mode, premium, alta densidad de información científica.
- **Vistas**:
    - **Panel de Riesgo**: Listado de atletas con semáforo de alerta.
    - **Análisis de Correlación**: Gráfico de dispersión IRI vs Desaceleraciones.
    - **Perfil de Neuro-evaluación**: Detalle por atleta.

## 4. Cronograma de Tareas
1. [ ] Inicialización de estructura de Cloud Functions (Python).
2. [ ] Implementación del Algoritmo IVN.
3. [ ] Configuración de Reglas de Seguridad de Firebase.
4. [ ] Creación del proyecto Flutter Web y diseño de UI Premium.
5. [ ] Integración de datos en tiempo real.
