# Documentación Técnica: Lógica de Calidad PPG (SNR)

Este documento describe cómo se calcula la calidad de la señal (Signal-to-Noise Ratio o SNR) en el módulo de biometría y cómo influye en la experiencia del usuario (UX) y la seguridad del hardware.

## 1. Cálculo de Calidad (SNR)

La función `calculateSignalQuality` en `PPGProcessor` evalúa la pureza de la señal roja capturada por la cámara en ventanas de 1 segundo (30 frames).

### Indicadores Clave:
- **Intensidad Media (`mean`):** Debe ser > 80. Si es menor, se asume que el flash no está cubierto o no hay flujo sanguíneo detectable (dedo mal posicionado).
- **Desviación Estándar (`stdDev`):**
    - `stdDev > 15.0`: Se detecta ruido excesivo por movimiento o luz ambiental filtrada. Calidad: **0.2 (Ruido)**.
    - `stdDev < 0.8`: Señal "plana". No se detectan picos de pulso. Calidad: **0.4 (Señal Débil)**.
    - `0.8 - 15.0`: Rango óptimo para detección de pulso. Calidad: **1.0 (Óptima)**.

## 2. Comportamiento de la barra de Estabilidad

La barra visual en `HrvCameraScreen` traduce estos valores para el usuario:

| Calidad (SNR) | Color | Mensaje UI | Acción del Sistema |
| :--- | :--- | :--- | :--- |
| **> 0.8** | Verde | "CAPTURA ÓPTIMA" | El progreso del test avanza. |
| **0.5 - 0.8** | Naranja | "INESTABLE" | El progreso se detiene para evitar datos corruptos. |
| **< 0.5** | Rojo | "SEÑAL PERDIDA" | El progreso se detiene y se avisa al usuario. |

## 3. Protocolos de Seguridad y Hardware

### Límite Estricto de 60 Segundos
El flash LED genera calor residual. Para proteger el sensor de la cámara y el dispositivo:
- Se inicia un **Timer de Seguridad** de 60s desde el encendido.
- Este timer **NO se detiene**, independientemente de la calidad de la señal.
- Al llegar a 0s, el flash se apaga automáticamente. Si no se recolectaron datos suficientes (25 intervalos R-R), el test se marca como fallido.

### Protección Térmica Reactiva
- Si el sistema detecta una excepción de tipo `thermalShutdown`, se bloquea el acceso a la cámara por 30s para permitir la disipación de calor.
