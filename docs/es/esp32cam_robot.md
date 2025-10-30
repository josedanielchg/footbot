## Robot ESP32-CAM (`esp32cam_robot/`) — Arquitectura y Operación

---

## Tabla de contenidos

- [Qué hace este módulo](#qué-hace-este-módulo)
- [Lenguajes y herramientas de compilación](#lenguajes-y-herramientas-de-compilación)
- [Estructura de carpetas (alto nivel)](#estructura-de-carpetas-alto-nivel)
- [Responsabilidades de archivos (resumen)](#responsabilidades-de-archivos-resumen)

---
### Qué hace este módulo
La ESP32-CAM aloja un **servidor web local** para que el portátil pueda **conectarse por Wi-Fi** y:
- **Enviar comandos de conducción** (avanzar/girar/detener) vía HTTP.
- **Obtener datos de cámara** como una imagen JPEG (`/capture`) o un **stream MJPEG** continuo (`/stream`).

Se inician dos servidores HTTP:
- **Control/Captura** en el **puerto 80** → rutas: `/`, `/status`, `/control`, `/capture`, `/move`.
- **Streaming** en el **puerto 81** → ruta: `/stream`.

El portátil ejecuta la lógica de percepción/decisión; la ESP32 se centra en **sensado + actuación de bajo nivel**.

---

### Lenguajes y herramientas de compilación
- **Lenguaje:** C++ con el **núcleo Arduino para ESP32** (usa internamente `esp_http_server` de ESP-IDF).
- **Construcción:** **Arduino IDE 2.x** (recomendado).  
  - Placa: **AI Thinker ESP32-CAM**.  
  - Habilitar **PSRAM** (si está disponible).  
  - Abre `esp32cam_robot/esp32cam_robot.ino` y **sube** el sketch.

---

### Estructura de carpetas (alto nivel)
```

esp32cam_robot/
├─ esp32cam_robot.ino      # Sketch principal (arranque, Wi-Fi, cámara, servidores)
├─ partitions.csv          # Mapa de particiones usado por el sketch
└─ src/
├─ handlers/             # Manejadores de rutas HTTP (cámara + control del robot)
├─ vendor/               # Cabeceras de terceros (p. ej., ArduinoJson.h)
├─ app_httpd.cpp         # Utilidades de cámara/stream (base de ejemplo ESP32)
├─ camera_index.h        # Página(s) HTML mínima(s) servidas en "/"
├─ camera_pins.h         # Mapa de pines de la placa (AI Thinker, etc.)
├─ config.h              # SSID/contraseña, puertos, GPIOs  ⟵ no subir secretos al VCS
├─ MotorControl.*        # Tracción diferencial (PWM + dirección)
├─ CameraController.*    # Inicialización de cámara y ajuste del sensor
├─ LedControl.*          # Control de LED de estado (si se usa)
├─ WifiManager.*         # Conexión a Wi-Fi
├─ WebRequestHandlers.*  # Agrega/inicializa manejadores de URI
└─ WebServerManager.*    # Inicia/detiene ambos servidores HTTP

```

> Las cargas útiles y la semántica detallada de la API aparecen en la sección de API. A continuación, un **mapa breve** del propósito principal de cada archivo.

---

### Responsabilidades de archivos (resumen)

| Ruta | Tipo | Propósito principal | Interfaz expuesta (funciones / endpoints) | Notas |
|---|---|---|---|---|
| `esp32cam_robot.ino` | Sketch | Secuencia de arranque; init LED y motores → cámara → Wi-Fi → arranque de servidores; imprime URLs; bucle inactivo | `setup()`, `loop()`, `measure_fps(int)` | Único lugar para cambiar orden de arranque/registro (logging). |
| `src/config.h` | Config | Configuración en compilación: modelo de cámara, **Wi-Fi SSID/PASS**, puertos HTTP, pines de motor/LED | macros: `WIFI_SSID`, `HTTP_CONTROL_PORT`, defines de pines | No publiques credenciales reales. |
| `src/CameraController.h` | Driver | Inicializa y ajusta la cámara; maneja PSRAM; fija tamaño/calidad inicial | `bool initCamera()`, `sensor_t* getCameraSensor()` | Predeterminados JPEG + QVGA para un streaming más fluido. |
| `src/MotorControl.h/.cpp` | Driver | Tracción diferencial con **LEDC PWM**; control de dirección | `setupMotors()`, `moveForward/Backward(int)`, `turnLeft/Right(int)`, `arcLeft/Right(int,float)`, `stopMotors()` | Usa canales de enable + pines IN por motor. |
| `src/WifiManager.h/.cpp` | Red | Unirse a la red Wi-Fi, desactivar sleep, imprimir IP, gestión de timeouts | `bool connectWiFi()` | Devuelve `false` si falla (~20 s). |
| `src/WebServerManager.h/.cpp` | Servidor | Inicia/detiene **dos** servidores HTTP y registra rutas | `bool startWebServer()`, `void stopWebServer()` | Control en **80** (`/`, `/status`, `/control`, `/capture`, `/move`); stream en **81** (`/stream`). |
| `src/WebRequestHandlers.h/.cpp` | Pegamento | Agrega/inicializa subsistemas de handlers | `initializeWebRequestHandlers()` | Incluye `handlers/camera_handlers.*` y `handlers/robot_control_handlers.*`. |
| `src/handlers/camera_handlers.h/.cpp` | Handlers | Implementa la web API de cámara | Endpoints: `"/"` → **index**, `"/status"` → JSON de estado, `"/control"` → parámetros de cámara (`var`,`val`), `"/capture"` → JPEG, `"/stream"` → MJPEG | Streaming usa boundary multipart; LED opcional durante captura/stream. |
| `src/handlers/robot_control_handlers.h/.cpp` | Handlers | Ejecuta comandos de movimiento recibidos por **HTTP POST JSON** | Endpoint: `"/move"` con `{direction, speed?, turn_ratio?}` → llama a `MotorControl` | Direcciones: `forward/backward/left/right/soft_left/soft_right/stop`. |
| `src/app_httpd.cpp` | Soporte | Utilidades heredadas del ejemplo de cámara ESP32 (codificar/servir frames) | helpers internos | Referenciado por los handlers de cámara. |
| `src/camera_index.h` | UI | HTML gzip para `/` (variantes según sensor) | servido por `indexHandler` | Página mínima de configuración/estado. |
| `src/camera_pins.h` | Mapa HW | Definición de pines para placas ESP32-CAM soportadas | macros | Se selecciona con `CAMERA_MODEL_*` en `config.h`. |
| `src/LedControl.*` | Driver | Control opcional del LED de estado/asistencia | `setupLed()`, `setLedIntensity(int)`, `controlLed(bool,int)`, `setLedStreamingState(bool)` | Usado por captura/stream para indicar actividad. |
| `src/vendor/ArduinoJson.h` | Terceros | Parseo de JSON para el cuerpo de `/move` | — | Cabecera incluida para portabilidad. |
| `partitions.csv` | Particiones | Tabla de particiones personalizada (OTA, NVS, coredump, etc.) | — | Necesaria para que quepan cámara + app OTA. |
| `ci.json` | CI/Matriz de build | Presets de FQBN para Arduino CLI (ESP32/ESP32-S2/S3; PSRAM, particiones) | — | Ayuda a builds reproducibles en automatización. |