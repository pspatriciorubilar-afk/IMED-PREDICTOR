# 🧠 AUDITORÍA TÉCNICA COMPLETA — IMED SNC (IMED Sport Neuro-Cognitive)
**Versión del Sistema:** 4.1.1 · **Fecha de Auditoría:** 2026-05-17  
**Destinatario:** Desarrollador Backend/DevOps — Ubuntu Linux  
**Propietario del proyecto:** Patricio Rubilar / IMED Sport

---

## 1. VISIÓN GENERAL DEL ECOSISTEMA

IMED SNC es una **plataforma de alto rendimiento deportivo** basada en la medición del Sistema Nervioso Central (SNC) mediante el test PVT *(Psychomotor Vigilance Task)*. El objetivo es que cada atleta realice una prueba de reacción diaria desde su celular y que el staff técnico visualice un semáforo de disponibilidad física en tiempo real.

```
┌──────────────────────────────────────────────────────────────┐
│                  ECOSISTEMA IMED SNC                         │
│                                                              │
│  📱 Flutter App (Android)                                    │
│     └─► PVT Test + Wellness Survey                           │
│         └─► POST /api/v3/metrics  ──► Express API            │
│                                       └─► BullMQ (Redis)     │
│                                           └─► Worker         │
│                                               └─► MySQL      │
│                                                              │
│  🌐 Dashboard Web (HTML/JS)                                  │
│     └─► GET /api/v3/dashboard/athletes ──► Express API       │
│                                           └─► MySQL          │
│                                                              │
│  🔥 Firebase (pipeline paralelo / IMED Predictor)            │
│     └─► Firestore (proyecto hermano)                         │
└──────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> El proyecto tiene **dos pipelines coexistiendo**:
> 1. **Pipeline IMED SNC** → Flutter → Express API → MySQL (esta auditoría)
> 2. **Pipeline IMED Predictor** → Flutter → Firebase/Firestore (proyecto hermano `/IMED PREDICTOR`)

---

## 2. ESTRUCTURA DE DIRECTORIOS

```
/IMED SNC/
├── lib/                            # App Flutter (Dart)
│   ├── main.dart                   # Entry point + Router principal
│   ├── core/
│   │   ├── biometrics/
│   │   │   ├── snc_engine.dart     # ⭐ Motor IRI (algoritmo principal)
│   │   │   └── ppg_snr_logic.md    # Notas PPG (sin implementar)
│   │   ├── network/                # Vacío – pendiente HTTP interceptor
│   │   └── services/               # Vacío – pendiente servicios globales
│   └── features/
│       ├── auth/
│       │   ├── domain/user_profile.dart
│       │   └── presentation/onboarding_screen.dart
│       ├── cognitive_load/
│       │   ├── application/
│       │   │   ├── pvt_notifier.dart      # ⭐ State machine PVT (Riverpod)
│       │   │   ├── pvt_data_source.dart   # Fuente de datos (Isar + API)
│       │   │   └── pvt_api_client.dart    # Cliente HTTP
│       │   ├── domain/
│       │   │   ├── pvt_session.dart       # Modelo Isar (DB local)
│       │   │   ├── pvt_session_metrics.dart
│       │   │   └── neuro_recommendations.dart
│       │   └── presentation/
│       │       ├── daily_readiness_screen.dart
│       │       ├── trends_screen.dart
│       │       └── widgets/pvt_test_widget.dart
│       ├── biometrics/
│       │   ├── domain/
│       │   │   ├── biometric_models.dart  # WellnessSurvey + BiometricPayload
│       │   │   └── zscore_algorithm.md
│       │   └── presentation/biometric_flow_coordinator.dart
│       └── education/
│           └── presentation/education_screen.dart
│
├── server/                         # Backend Node.js
│   ├── index.js                    # ⭐ API Express (entrada principal)
│   ├── Dockerfile                  # Imagen multi-stage node:18-alpine
│   ├── package.json                # Dependencias npm v2.1.0
│   ├── .env.example                # Variables de entorno requeridas
│   ├── db_schema.sql               # Schema SQL legacy (solo referencia)
│   ├── prisma/schema.prisma        # ⭐ Schema Prisma MySQL (fuente de verdad)
│   ├── services/
│   │   ├── pvt_queue.js            # ⭐ Worker BullMQ (procesamiento asíncrono)
│   │   ├── neuro_engine.js         # Motor Z-score (no integrado aún)
│   │   ├── prisma.js               # Singleton PrismaClient
│   │   └── load_test.js            # Script de prueba de carga
│   └── middleware/                 # Pendiente de inspección
│
├── dashboard/                      # Dashboard Web v1 (staff técnico)
│   ├── index.html                  # HTML semáforo de disponibilidad
│   ├── dashboard.css               # Estilos dark glassmorphism
│   └── dashboard_app.js            # Fetch + render tabla atletas
│
├── dashboard-v2/src/               # Dashboard v2 (en desarrollo, vacío)
├── docker-compose.yml              # Stack: API + Redis
├── nginx.conf                      # Reverse proxy → localhost:3000
└── pubspec.yaml                    # Dependencias Flutter v4.1.1
```

---

## 3. STACK TECNOLÓGICO COMPLETO

### 3.1 App Móvil (Cliente)
| Tecnología | Versión | Rol |
|---|---|---|
| Flutter | SDK ≥3.0.0 | Framework UI multiplataforma |
| flutter_riverpod | ^2.5.1 | State management |
| Isar | ^3.1.0 | DB local offline-first (NoSQL) |
| Hive | ^2.2.3 | Persistencia simple (sync queue) |
| firebase_core | ^2.31.0 | Inicialización Firebase |
| cloud_firestore | ^4.17.4 | Pipeline alternativo |
| fl_chart | ^0.65.0 | Gráficas de tendencias |
| flutter_local_notifications | ^17.2.4 | Notificaciones circadianas |
| workmanager | ^0.5.2 | Background sync |
| http | ^1.2.1 | Cliente HTTP REST |
| camera | ^0.11.0 | Cámara (PPG – sin implementar) |
| sensors_plus | ^5.0.1 | Acelerómetro/giroscopio |

### 3.2 Backend (Servidor)
| Tecnología | Versión | Rol |
|---|---|---|
| Node.js | 18 Alpine | Runtime |
| Express | ^4.18.2 | Framework HTTP |
| Prisma | ^5.10.2 | ORM – MySQL |
| MySQL | 8+ | Base de datos relacional |
| BullMQ | ^5.76.5 | Cola de trabajos asíncronos |
| ioredis | ^5.10.1 | Cliente Redis |
| Redis | 7-alpine | Message broker para BullMQ |
| jsonwebtoken | ^9.0.2 | Autenticación JWT |
| helmet | ^7.1.0 | Seguridad HTTP headers |
| cors | ^2.8.5 | Cross-Origin |
| express-rate-limit | ^7.1.5 | Rate limiting |

### 3.3 Infraestructura / DevOps
| Componente | Tecnología |
|---|---|
| Contenedores | Docker + Docker Compose |
| Reverse Proxy | Nginx |
| IP servidor actual | `92.112.179.19` (hardcodeada en dashboard_app.js) |
| Dominio previsto | `api.imedsport.com` / `dashboard.imedsport.com` |

---

## 4. BASE DE DATOS — SCHEMA PRISMA (MySQL)

**Fuente de verdad:** `server/prisma/schema.prisma`  
**ORM:** Prisma 5 con MySQL  
**Total de modelos:** 18

```
User ──────── PvtResult (1:N)   ← Tabla operacional principal
  ├─ AthleteProfile
  ├─ CoachProfile
  └─ PsychologistProfile

AthleteProfile
  ├─ Evaluation → Score + Answer
  ├─ ClinicalNote
  ├─ Intervention
  ├─ FollowUpPlan
  └─ Alert

Club ── Team ── AthleteProfile ── CoachProfile
```

### Tabla central: `PvtResult`
```prisma
model PvtResult {
  id                   Int             @id @default(autoincrement())
  userId               String
  timestamp            DateTime        @default(now())
  meanLatency          Float           // latencia media en ms
  lapsesCount          Int             // respuestas > 500ms
  falseStarts          Int             // falsas anticipaciones
  rawMetrics           Json?           // array completo de tiempos
  sleepHours           Float           // horas de sueño
  sleepQuality         Int             // 1-5
  stressLevel          Int             // 1-5
  fatigueLevel         Int             // 1-5
  average_latency_7d   Float           // línea base 7 días
  deviation_percentage Float           // % desviación vs baseline
  status_color         ReadinessStatus // GREEN | YELLOW | RED
  deletedAt            DateTime?       // soft delete
  @@index([userId, timestamp])
}
```

> [!NOTE]
> El archivo `db_schema.sql` es un schema **legacy** de referencia. **No ejecutar en producción.** Usar `npx prisma migrate deploy`.

---

## 5. API REST — ENDPOINTS ACTIVOS

**Base URL:** `http://92.112.179.19`  
**Auth:** JWT Bearer Token

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/api/v3/auth/login` | ❌ | Login por athleteId → devuelve JWT |
| `POST` | `/api/v3/metrics` | ✅ | Ingesta PVT + Wellness → BullMQ |
| `GET` | `/api/v3/readiness` | ✅ | Estado actual del atleta |
| `GET` | `/api/v3/trends` | ✅ | Historial 7 días |
| `GET` | `/api/v3/dashboard/athletes` | ❌ | Lista atletas con estado (dashboard) |
| `GET` | `/dashboard/*` | ❌ | Archivos estáticos del Dashboard HTML |

### Payload `POST /api/v3/metrics`
```json
{
  "athleteId": "sofia.torres@imed.cl",
  "sleep_hours": 7.5,
  "sleep_quality": 4,
  "stress_level": 2,
  "fatigue_level": 2,
  "pvt_logs": [280, 310, 295, 340, 270, 390, 260, 305, 288, 320]
}
```

### Respuesta `GET /api/v3/readiness`
```json
{
  "status": "GREEN",
  "readinessScore": 90,
  "message": "SNC en equilibrio. Carga recomendada: ALTA.",
  "diagnostics": {
    "deviation": "3.2",
    "latency": "295.0",
    "baseline7d": "285.5"
  }
}
```

---

## 6. ALGORITMO CENTRAL — IRI (Índice de Resiliencia Neural)

### Fórmula completa (`lib/core/biometrics/snc_engine.dart`)
```
IRIFinal = IRIBase × contextModifier

IRIBase:
  pvtScore = (100 - ((meanPvt - 250) / 250) × 100).clamp(0, 100)
  • 250ms = élite (100 pts)
  • 500ms = fatiga extrema (0 pts)

contextModifier = 0.80 + (contextScore × 0.28)   → rango [0.80 – 1.08]
  contextScore = (sleepHoursFactor × 0.35)
              + (sleepQualityFactor × 0.25)
              + (stressInverseFactor × 0.20)
              + (fatigueInverseFactor × 0.20)
  • sleepHours: óptimo 8h=1.0, mínimo 5h=0.0, <5h: degradación acelerada
  • sleepQuality/stress/fatigue: escala 1-5 normalizada
```

### Semáforo de disponibilidad
| IRI | Estado | Color | Prescripción |
|---|---|---|---|
| ≥85 | READY / Óptimo | 🟢 VERDE | Alta carga, intensidad máxima |
| 70–84 | CAUTION / Precaución | 🟡 AMARILLO | Carga moderada, monitoreo |
| 50–69 | FATIGUE / Fatiga | 🟠 NARANJA | Reducir carga |
| <50 | EXHAUSTED / Crítico | 🔴 ROJO | Recuperación total |

### Algoritmo en servidor (`server/services/pvt_queue.js`)
```
Si sessionCount < 7 → COLD START → status = GREEN

Si sessionCount ≥ 7:
  sevenDayAvg = media de latencias últimos 7 días
  deviation = ((meanLatency - sevenDayAvg) / sevenDayAvg) × 100

  deviation > 15% OR lapses > 2  → RED
  deviation > 10%                → YELLOW
  else                           → GREEN
```

> [!NOTE]
> `neuro_engine.js` implementa un **Z-score adaptativo** (14 sesiones, stdDev) más preciso, pero actualmente **no está conectado** al pipeline principal.

---

## 7. FLUJO COMPLETO DE UNA SESIÓN

```
[1] Atleta abre la app Flutter
[2] BiometricFlowCoordinator → pantalla de bienvenida
[3] Wellness Survey (sleepHours, sleepQuality, stressLevel, fatigueLevel)
[4] PVT Test (PvtNotifier – Riverpod StateNotifier)
    • 10 estímulos con ISI aleatorio 1.5–4 segundos
    • Captura tiempos de reacción en ms
    • Filtra false starts (<120ms) y lapses (>500ms)
    • Guarda sesión en Isar local (isSynced: false)
[5] POST /api/v3/metrics → Express (JWT auth)
    • Calcula meanLatency y lapsesCount
    • Agrega job a Cola BullMQ 'pvt-ingest'
    • Responde 201 inmediatamente (no bloquea UI)
[6] Worker BullMQ procesa el job:
    • Upsert del User en MySQL
    • Cold start check (< 7 sesiones)
    • Calcula sevenDayAvg y deviation_percentage
    • Asigna status_color (GREEN/YELLOW/RED)
    • Persiste PvtResult en MySQL
    • Si RED → genera alerta en cola 'pvt-alerts'
[7] Alert Worker → log + notificación staff
    (pendiente: email/SMS/push real)
[8] Dashboard Web consulta cada 30s:
    GET /api/v3/dashboard/athletes → semáforo del equipo
```

---

## 8. APP FLUTTER — MÓDULOS DE NAVEGACIÓN

| Índice | Pestaña | Widget | Estado |
|---|---|---|---|
| 0 | 🧠 Prueba PVT | `BiometricFlowCoordinator` | ✅ Funcional |
| 1 | 💓 Registro Diario | `DailyReadinessScreen` | ✅ Funcional |
| 2 | 📊 Historial | `TrendsScreen` | ✅ Funcional (fl_chart) |
| 3 | 🎓 Educación | `EducationScreen` | ✅ Funcional (estático) |

**Primer uso:** Si no hay `UserProfile` en Isar → `OnboardingScreen` → guarda perfil → `MainModuleSelector`

**Almacenamiento local:**
- `Isar`: `PvtSession`, `UserProfile` (datos estructurados)
- `Hive`: `sync_queue` (sesiones pendientes), `daily_readiness`

---

## 9. VARIABLES DE ENTORNO REQUERIDAS

Archivo: `server/.env`

```env
DATABASE_URL="mysql://USER:PASSWORD@HOST:3306/imed_sport_db"
JWT_SECRET="CADENA_DE_SEGURIDAD_IMED_SPORT_2026"
REDIS_URL="redis://127.0.0.1:6379"
PORT=3000
```

---

## 10. DESPLIEGUE EN UBUNTU LINUX

### Prerrequisitos del sistema
```bash
# Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# MySQL 8
sudo apt install mysql-server && sudo mysql_secure_installation

# Redis
sudo apt install redis-server && sudo systemctl enable redis-server

# Docker + Compose (opción alternativa)
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
```

### Opción A — Docker Compose (recomendado)
```bash
# 1. Copiar el proyecto al servidor
scp -r ./server user@servidor:/opt/imed-snc/

# 2. Configurar variables de entorno
cp server/.env.example server/.env && nano server/.env

# 3. Levantar stack completo (API + Redis)
docker-compose up -d --build

# 4. Migraciones Prisma (primera vez)
docker exec imed-api npx prisma migrate deploy

# 5. Verificar
curl http://localhost:3000/api/v3/dashboard/athletes
```

### Opción B — Despliegue manual con PM2
```bash
cd /opt/imed-snc/server
npm install
npx prisma generate
npx prisma migrate deploy    # o: npx prisma db push (dev)

# Producción con PM2
npm install -g pm2
pm2 start index.js --name imed-api
pm2 startup && pm2 save
```

### Nginx
```bash
sudo cp nginx.conf /etc/nginx/sites-available/imed-snc
sudo ln -s /etc/nginx/sites-available/imed-snc /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 11. ESTADO ACTUAL DE CADA COMPONENTE

| Componente | Estado | Observación |
|---|---|---|
| PVT Test (Flutter) | ✅ Completo | 10 estímulos, ISI aleatorio, false starts |
| Wellness Survey | ✅ Completo | 4 variables integradas al payload |
| SNC Engine / IRI | ✅ Completo | Algoritmo local Dart, fórmula ponderada |
| Almacenamiento Isar | ✅ Completo | Offline-first |
| Sync con API REST | ⚠️ Parcial | Cliente HTTP listo, sync queue incompleta |
| API Express | ✅ Funcional | 6 endpoints activos |
| Worker BullMQ | ✅ Funcional | Calcula status, persiste en MySQL |
| MySQL + Prisma | ✅ Completo | 18 modelos, schema listo |
| Dashboard Web v1 | ✅ Funcional | Semáforo básico sin autenticación |
| Dashboard Web v2 | 🚧 Vacío | Directorio existe, sin contenido |
| Alertas al staff | ⚠️ Parcial | Worker existe, solo console.log |
| Auth en dashboard | ❌ Faltante | Endpoint público sin JWT |
| neuro_engine.js | ⚠️ No integrado | Código listo, desconectado |
| Firebase/Firestore | ✅ Paralelo | Usado por IMED Predictor |
| PPG por cámara | ❌ No implementado | Librería incluida, sin lógica |

---

## 12. DEUDA TÉCNICA PRIORIZADA

### Alta prioridad
1. **Proteger `/api/v3/dashboard/athletes`** — Agregar JWT o API Key (riesgo de privacidad)
2. **Background sync Flutter** — Completar `workmanager` para sincronizar Isar → API offline
3. **Integrar `neuro_engine.js`** — Reemplazar lógica en `pvt_queue.js` con Z-score adaptativo
4. **Alertas reales** — Conectar Alert Worker a email (nodemailer) o push

### Media prioridad
5. **Filtro por equipo** — Implementar lógica real en backend (GET con query param)
6. **`falseStarts` en payload** — Hardcodeado a `0` en `index.js` línea 81
7. **Dashboard v2** — Desarrollar interfaz mejorada
8. **`age: 25`** en pvt_queue.js — Hardcodeado, debería venir del perfil del atleta

### Baja prioridad
9. **Login real** — Auth actual es un `upsert` sin validación de contraseña
10. **PPG por cámara** — Funcionalidad futura (HRV por cámara trasera)

---

## 13. CONEXIÓN CON IMED PREDICTOR

El proyecto hermano `/IMED PREDICTOR/` es un dashboard web (HTML + JS puro) con **Firebase/Firestore** como backend, actualmente en producción con datos reales.

| Aspecto | IMED SNC | IMED Predictor |
|---|---|---|
| Stack backend | Node.js + MySQL | Firebase/Firestore |
| Dashboard | HTML/JS servido por Express | HTML/JS estático |
| Pipeline datos | Flutter → Express → MySQL | Flutter → Cloud Functions → Firestore |
| Estado | En integración | En producción activa |
| Objetivo futuro | Backend unificado | Migrar a IMED SNC |

---

---

## 14. INTEGRACIÓN DE ANÁLISIS EX-GAUSSIANO Y RESILIENCIA DE CACHÉ

### 14.1 Estado de Implementación
* **Status:** `COMPLETED & RESILIENT`
* **Cambios Clave:**
  1. **Dashboard Visual (Modal SNC):** Se integró el panel de traducción de variables Ex-Gaussianas (μ, σ, τ) y la visualización de los datos clínicos reales calculados por el worker.
  2. **Bypass de Calibración Resiliente:** Se corrigió una vulnerabilidad de lógica en `app_v411_final.js` donde un estado residual `'INSUFFICIENT_TRIALS'` de Firestore (debido a fusiones previas con `merge: true`) bloqueaba la visualización de datos válidos. El condicional ahora valida la existencia de `mu_ms`:
     `if (!aa || (aa.status === 'INSUFFICIENT_TRIALS' && aa.mu_ms == null))`
  3. **Control de Caché del Navegador:** Se incrementó el query-param de versión en `index.html` a `v=4.14.8` para forzar a todos los navegadores a recargar inmediatamente el script JavaScript sin depender del almacenamiento en caché del cliente.
  4. **Prueba Sincronizada (Patricio Rubilar - 2026-05-19):** Datos verificados en producción y desplegados con éxito en [https://app-imed-sport.web.app](https://app-imed-sport.web.app):
     * **μ (Velocidad Motora Base):** `209.4ms`
     * **σ (Consistencia Cognitiva):** `2.5ms`
     * **τ (Fatiga Central / Cola):** `34.8ms`

*Documento actualizado por Antigravity AI · IMED Sport Ecosystem v4.13.0 · 2026-05-19*
