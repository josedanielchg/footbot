## ESP32-CAM robot (`esp32cam_robot/`) — Architecture & Operation
---
### What this module does
The ESP32-CAM hosts a **local web server** so the laptop can **connect over Wi-Fi** to:
- **Send drive commands** (move/turn/stop) via HTTP.
- **Retrieve camera data** as a single JPEG (`/capture`) or a continuous **MJPEG stream** (`/stream`).

Two HTTP servers are launched:
- **Control/Capture** on **port 80** → routes: `/`, `/status`, `/control`, `/capture`, `/move`.
- **Streaming** on **port 81** → route: `/stream`.

The laptop runs the perception/decision logic; the ESP32 focuses on **sensing + low-level actuation**.

---

### Languages & build tools
- **Language:** C++ with the **Arduino core for ESP32** (uses ESP-IDF’s `esp_http_server` internally).
- **Build:** **Arduino IDE 2.x** (recommended).  
  - Board: **AI Thinker ESP32-CAM**.  
  - Enable **PSRAM** (if available).  
  - Open `esp32cam_robot/esp32cam_robot.ino` and **Upload**.

---

### Folder structure (high level)
```

esp32cam_robot/
├─ esp32cam_robot.ino      # Main sketch (boot, Wi-Fi, camera, servers)
├─ partitions.csv          # Flash layout used by the sketch
└─ src/
    ├─ handlers/             # HTTP route handlers (camera + robot control)
    ├─ vendor/               # Third-party headers (e.g., ArduinoJson.h)
    ├─ app_httpd.cpp         # Camera/stream helpers (ESP32 example base)
    ├─ camera_index.h        # Minimal HTML page(s) served at "/"
    ├─ camera_pins.h         # Board pin map (AI Thinker, etc.)
    ├─ config.h              # SSID/password, ports, GPIOs  ⟵ keep secrets out of VCS
    ├─ MotorControl.*        # Differential drive (PWM + direction)
    ├─ CameraController.*    # Camera init & sensor tuning
    ├─ LedControl.*          # Status LED control (if used)
    ├─ WifiManager.*         # Wi-Fi bring-up
    ├─ WebRequestHandlers.*  # Aggregates/initializes URI handlers
    └─ WebServerManager.*    # Starts/stops both HTTP servers

```

> Endpoint payloads and detailed API semantics appear in the API section. Below is a **brief map** of each file’s principal purpose.

---

### File responsibilities (summary)

| Path | Kind | Principal purpose | Exposed interface (functions / endpoints) | Notes |
|---|---|---|---|---|
| `esp32cam_robot.ino` | Sketch | Boot sequence; init LED & motors → camera → Wi-Fi → start servers; prints URLs; idle loop | `setup()`, `loop()`, `measure_fps(int)` | Single place to change boot order/logging. |
| `src/config.h` | Config | Compile-time configuration: camera model, **Wi-Fi SSID/PASS**, HTTP ports, motor/LED pins | macros: `WIFI_SSID`, `HTTP_CONTROL_PORT`, pin defines | Don’t commit real credentials. |
| `src/CameraController.h` | Driver | Bring-up and tune camera; handle PSRAM; set initial framesize/quality | `bool initCamera()`, `sensor_t* getCameraSensor()` | JPEG + QVGA defaults for smoother streaming. |
| `src/MotorControl.h/.cpp` | Driver | Differential drive with **LEDC PWM**; direction control | `setupMotors()`, `moveForward/Backward(int)`, `turnLeft/Right(int)`, `arcLeft/Right(int,float)`, `stopMotors()` | Uses enable channels + IN pins per motor. |
| `src/WifiManager.h/.cpp` | Net | Join Wi-Fi network, disable sleep, print IP, timeout handling | `bool connectWiFi()` | Returns `false` on failure (~20s). |
| `src/WebServerManager.h/.cpp` | Server | Start/stop **two** HTTP servers and register routes | `bool startWebServer()`, `void stopWebServer()` | Control on **80** (`/`, `/status`, `/control`, `/capture`, `/move`); stream on **81** (`/stream`). |
| `src/WebRequestHandlers.h/.cpp` | Glue | Aggregate/init handler subsystems | `initializeWebRequestHandlers()` | Includes `handlers/camera_handlers.*` and `handlers/robot_control_handlers.*`. |
| `src/handlers/camera_handlers.h/.cpp` | Handlers | Implement camera web API | Endpoints: `"/"` → **index**, `"/status"` → JSON status, `"/control"` → camera params (`var`,`val`), `"/capture"` → JPEG, `"/stream"` → MJPEG | Streaming uses multipart boundary; optional LED assist on capture/stream. |
| `src/handlers/robot_control_handlers.h/.cpp` | Handlers | Execute motion commands received via HTTP **POST JSON** | Endpoint: `"/move"` with `{direction, speed?, turn_ratio?}` → calls `MotorControl` | Directions: `forward/backward/left/right/soft_left/soft_right/stop`. |
| `src/app_httpd.cpp` | Support | Helper utilities from ESP32 camera example (encoding/serving frames) | internal helpers | Referenced by camera handlers. |
| `src/camera_index.h` | UI | Gzipped HTML for `/` (sensor-specific variants) | served by `indexHandler` | Tiny configuration/status page. |
| `src/camera_pins.h` | HW map | Pin definitions for supported ESP32-CAM boards | macros | Selected by `CAMERA_MODEL_*` in `config.h`. |
| `src/LedControl.*` | Driver | Optional status/assist LED control | `setupLed()`, `setLedIntensity(int)`, `controlLed(bool,int)`, `setLedStreamingState(bool)` | Used by capture/stream to signal activity. |
| `src/vendor/ArduinoJson.h` | Third-party | JSON parsing for `/move` body | — | Bundled header for portability. |
| `partitions.csv` | Flash layout | Custom partition table (OTA slot, NVS, coredump, etc.) | — | Needed to fit camera + OTA app. |
| `ci.json` | CI/Build matrix | Arduino CLI FQBN presets (ESP32/ESP32-S2/S3; PSRAM, partitions) | — | Helps reproducible builds in automation. |