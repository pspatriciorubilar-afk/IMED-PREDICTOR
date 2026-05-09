# IMED Predictor — SaaS de Prevención de Lesiones

Ecosistema de monitoreo de rendimiento de élite que integra métricas neuro-cognitivas (IMED Sport) con datos de carga mecánica (GPS) mediante el algoritmo **$IVN$ (Índice de Vulnerabilidad Neuro-Mecánica)**.

## 🚀 Características
- **Dashboard Elite**: Interfaz basada en Glassmorphism con monitoreo en tiempo real.
- **Motor IVN**: Lógica en Cloud Functions (Python) para la predicción de riesgos de lesiones.
- **Adaptador GPS**: Procesamiento agnóstico de archivos CSV (Oliver, UC-CENDIA, etc.).
- **Integración Firebase**: Firestore, Storage y Hosting configurados.

## 🛠️ Tecnologías
- **Frontend**: HTML5, Vanilla CSS, JavaScript (Firebase SDK v10).
- **Backend**: Google Cloud Functions (Python 3.13).
- **Base de Datos**: Firestore (NoSQL).
- **Análisis de Datos**: Pandas.

## 📦 Despliegue
Para desplegar el proyecto en un nuevo entorno Firebase:
```bash
firebase deploy
```

## 🔐 Seguridad
Los datos de los atletas en la colección `athletes/` son de **Solo Lectura** para proteger la integridad de la App móvil original. El análisis se centraliza en la colección `Daily_Performance`.

---
*Desarrollado para IMED Sport — 2026*
