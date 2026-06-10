# IMED SPORT SNC v2.0 - Neuro-Performance Ecosytem

![Nivel 3 Dashboard Mockup](https://lh3.googleusercontent.com/aida/ADBb0ujLtQ6dhkoA5IYBYHrM-JGC3QujRjrm41uY4lvieB6bjtF6_3pPB-E89St7xLW0g5834jnnBcWU0mf-4-uWuKxTTiQnMJ8Jx-w5TrhDlI_GRAvYkFCAKeAhpGd8YZ_70isEajNTgeqS7VpHIyzsCmDHAa8sOCljtmaXQ2uFiTyVOtTwC75xrN4AT2CcyxsdshjF0238dLj2fBvXK2V7mrPAVaASkN47QM0bD3kt4TviwOMYG1TXuwvFslYq)

IMED SPORT SNC es una plataforma de telemetría clínica diseñada para atletas de élite, que permite trackear la carga cognitiva mediante pruebas de Vigilancia Psicomotora (PVT) y percepción de bienestar (Wellness).

## 🚀 Arquitectura del Sistema
El ecosistema está compuesto por tres capas principales:

### 1. Frontend: Flutter App (Mobile HUD)
*   **Estética HUD:** Interfaz premium en dark mode con alta precisión de visualización.
*   **Captura PPG:** Algoritmo propietario para HRV mediante cámara flash (vía Camera API).
*   **Motor Cognitivo:** Implementación de Psychomotor Vigilance Task (PVT).

### 2. Backend: Node.js API (Cerebro Estadístico)
*   **Framework:** Express.js + Prisma ORM.
*   **Motor Estadístico:** Cálculo de Z-Scores, Baseline de 7 días y "Fase de Choque" para recalibración automática.
*   **Base de Datos:** MySQL (Hosting en Hostinger).
*   **Caché:** Redis para gestión de colas y Rate Limiting.

### 3. Infraestructura: Dockerized Environment
*   Preparado para despliegue via Docker Compose.
*   Pipeline de despliegue automatizado hacia Hostinger (`neuro.elitemindpro.com`).

---

## 🛠️ Guía de Instalación Rápida

### Requisitos Previos
*   Flutter SDK (3.x+)
*   Node.js (18+)
*   MySQL Server (o cuenta Hostinger activa)

### Configuración del Backend
1. Entrar en la carpeta `server/`.
2. Crear un archivo `.env` (basado en `.env.example`).
3. Instalar dependencias: `npm install`.
4. Sincronizar DB: `npx prisma db push`.
5. Iniciar: `npm run dev`.

### Configuración del App (Flutter)
1. Ejecutar `flutter pub get`.
2. Actualizar la `baseUrl` en `lib/core/network/sync_service.dart`.
3. Compilar para Android: `flutter build apk --release`.

---

## 📡 Diccionario de Endpoints (API v3.2)

### Autenticación
*   `POST /api/v3/auth/login`: Autentificación del atleta mediante `athleteId`.

### Biometría e Ingesta
*   `POST /api/v3/metrics`: Envío masivo de métricas (PVT, HRV, Wellness).
*   `GET /api/v3/readiness`: CPU de Diagnóstico. Devuelve el estado (Verde/Amarillo/Rojo), Score (0-100) y advertencias de calidad (SNR).
*   `GET /api/v3/trends`: Recupera los últimos 7 días de telemetría para gráficas HUD.

---

## 🔒 Gestión de Secretos
Este repositorio está preparado para usar **GitHub Secrets**. Asegúrate de configurar las siguientes variables en el panel de Actions:
*   `DATABASE_URL`: String de conexión MySQL.
*   `JWT_SECRET`: Llave de firma para tokens JWT.

---
**Desarrollado por el equipo IMED SPORT - Nivel 3 Analytics Ready.**
