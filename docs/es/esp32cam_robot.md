## ESP32-CAM robot (`esp32cam_robot/`) — Arquitectura y Operación
---

### Qué hace este módulo
La ESP32-CAM ejecuta un **servidor web local** para que el portátil se conecte por **Wi-Fi** y pueda:
- **Enviar órdenes de movimiento** (avanzar, girar, parar) por HTTP.
- **Obtener datos de cámara** como una captura JPEG (`/capture`) o un **stream MJPEG** continuo (`/stream`).

Se lanzan dos servidores HTTP:
- **Control/Captura** en el **puerto 80** → rutas: `/`, `/status`, `/control`, `/capture`, `/move`.
- **Streaming** en el **puerto 81** → ruta: `/stream`.

El portátil realiza la percepción y la decisión; la ESP32 se encarga del **sensado y la actuación de bajo nivel**.

---

### Lenguajes y herramientas de compilación
- **Lenguaje:** C++ con el **núcleo Arduino para ESP32** (usa `esp_http_server` de ESP-IDF).
- **Compilación:** **Arduino IDE 2.x** (recomendado).  
  - Placa: **AI Thinker ESP32-CAM**.  
  - Activar **PSRAM** (si está disponible).  
  - Abrir `esp32cam_robot/esp32cam_robot.ino` y **Subir**.

---

### Estructura de carpetas (alto nivel)
```

esp32cam_robot/
├─ esp32cam_robot.ino      # Sketch principal (boot, Wi-Fi, cámara, servidores)
├─ partitions.csv          # Layout de memoria flash
└─ src/
  ├─ handlers/             # Manejadores HTTP (cámara + control del robot)
  ├─ vendor/               # Cabeceras de terceros (p. ej., ArduinoJson.h)
  ├─ app_httpd.cpp         # Soporte cámara/stream (base ejemplo ESP32)
  ├─ camera_index.h        # Página(s) HTML servidas en "/"
  ├─ camera_pins.h         # Mapa de pines de la placa
  ├─ config.h              # SSID/clave, puertos, GPIOs  ⟵ no subir secretos
  ├─ MotorControl.*        # Tracción diferencial (PWM + dirección)
  ├─ CameraController.*    # Inicialización de cámara y *tuning*
  ├─ LedControl.*          # LED de estado (si se usa)
  ├─ WifiManager.*         # Conexión Wi-Fi
  ├─ WebRequestHandlers.*  # Agregador/inicializador de *handlers*
  └─ WebServerManager.*    # Arranque/parada de ambos servidores HTTP

```

> Las cargas útiles y la semántica de cada endpoint están en la sección de API. Abajo solo se mapea el **propósito principal** de cada archivo.

---

### Responsabilidades de archivos (resumen)

| Ruta | Tipo | Propósito principal | Interfaz expuesta (funciones / endpoints) | Notas |
|---|---|---|---|---|
| `esp32cam_robot.ino` | Sketch | Secuencia de arranque; init LED y motores → cámara → Wi-Fi → servidores; imprime URLs; bucle inactivo | `setup()`, `loop()`, `measure_fps(int)` | Único lugar para ordenar el *boot* y *logging*. |
| `src/config.h` | Config | Configuración de compilación: modelo de cámara, **SSID/clave**, puertos HTTP, pines de motor/LED | macros: `WIFI_SSID`, `HTTP_CONTROL_PORT`, etc. | No subas credenciales reales. |
| `src/CameraController.h` | Driver | Puesta en marcha y ajuste del sensor; maneja PSRAM; framesize/calidad inicial | `bool initCamera()`, `sensor_t* getCameraSensor()` | JPEG + QVGA por defecto para *streaming* fluido. |
| `src/MotorControl.h/.cpp` | Driver | Tracción diferencial con **PWM LEDC** y control de dirección | `setupMotors()`, `moveForward/Backward(int)`, `turnLeft/Right(int)`, `arcLeft/Right(int,float)`, `stopMotors()` | Usa canales *enable* + pines IN por motor. |
| `src/WifiManager.h/.cpp` | Red | Unión a la Wi-Fi, *sleep* desactivado, impresión de IP, *timeout* | `bool connectWiFi()` | Devuelve `false` tras ~20 s si falla. |
| `src/WebServerManager.h/.cpp` | Servidor | Arranque/parada de **dos** servidores HTTP y registro de rutas | `bool startWebServer()`, `void stopWebServer()` | Control **80**: `/`, `/status`, `/control`, `/capture`, `/move` · Stream **81**: `/stream`. |
| `src/WebRequestHandlers.h/.cpp` | Glue | Agrega e inicializa subsistemas de *handlers* | `initializeWebRequestHandlers()` | Incluye `handlers/camera_handlers.*` y `handlers/robot_control_handlers.*`. |
| `src/handlers/camera_handlers.h/.cpp` | Handlers | Implementación del API de cámara | Endpoints: `"/"` (index), `"/status"` (JSON), `"/control"` (parámetros), `"/capture"` (JPEG), `"/stream"` (MJPEG) | LED opcional durante captura/stream. |
| `src/handlers/robot_control_handlers.h/.cpp` | Handlers | Ejecución de órdenes de movimiento vía **POST JSON** | Endpoint: `"/move"` con `{direction, speed?, turn_ratio?}` → `MotorControl` | Direcciones: `forward/backward/left/right/soft_* / stop`. |
| `src/app_httpd.cpp` | Soporte | Utilidades del ejemplo de cámara ESP32 (codificación/servicio de frames) | — | Usado por los *handlers* de cámara. |
| `src/camera_index.h` | UI | HTML comprimido servido en `/` (según sensor) | servido por `indexHandler` | Página de configuración/estado. |
| `src/camera_pins.h` | HW | Definiciones de pines para placas soportadas | macros | Seleccionado por `CAMERA_MODEL_*` en `config.h`. |
| `src/LedControl.*` | Driver | Control del LED de estado/asistencia | `setupLed()`, `setLedIntensity(int)`, `controlLed(bool,int)`, `setLedStreamingState(bool)` | Integrado con captura/stream. |
| `src/vendor/ArduinoJson.h` | Terceros | Parser JSON para el cuerpo de `/move` | — | Cabecera incluida para portabilidad. |
| `partitions.csv` | Memoria | Tabla de particiones (OTA, NVS, coredump, etc.) | — | Necesaria para cámara + OTA. |
| `ci.json` | Build/CI | *Presets* de Arduino CLI (ESP32/S2/S3; PSRAM, particiones) | — | Para *builds* reproducibles. |

---