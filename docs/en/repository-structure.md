## Repository structure

The codebase is split into **four top-level modules**, each owning a distinct part of the system. Documentation lives in `docs/` and deeper, per-module guides follow in later sections.

---

## Table of Contents

- [Top-level modules](#top-level-modules)
- [Languages & tooling](#languages--tooling)
- [Python environments (one per host-side module)](#python-environments-one-per-host-side-module)

---

### Top-level modules

- **`esp32cam_robot/` — Embedded firmware (on-robot)**
  - ESP32-CAM firmware exposing **HTTP control endpoints** and **video streaming**.
  - Subsystems: Wi-Fi provisioning, web server & request handlers, motor/LED drivers, camera control.
  - **Language/Tooling:** C++ (Arduino core for ESP32), Arduino IDE or PlatformIO.

- **`manual_control/` — Gesture-driven teleoperation (host)**
  - Webcam capture, **hand/gesture detection & classification**, command mapping, HTTP client to robot.
  - **Language/Tooling:** Python; see `requirements.txt` for vision/runtime deps.
  - Entry point: `main.py`.

- **`auto_soccer_bot/` — Automatic mode (host autonomy)**
  - ESP32-CAM stream ingestion, **ball detection**, decision logic (**ball follower implemented**), HTTP client.
  - Bundles exported YOLO weights under `models/` for local runs.
  - **Language/Tooling:** Python; entry point `main.py`.

- **`soccer_vision/` — Model training & evaluation (YOLOv11, 2 classes: `goal` & `opponent`)**
  - Dataset layout (`train/`, `val/`), training CLI & notebooks, quick inference tester, and **artifacts** (curves, confusion matrices, saved weights).
  - **Language/Tooling:** Python with the Ultralytics/YOLO stack (see `requirements.txt`).

<br>

> Supporting folders
> - **`docs/`**: multilingual documentation (`en/`, `es/`, `fr/`).  
> - **`LICENSE` / `README.md`**: licensing and high-level overview.

---

### Languages & tooling (expanded)

- **Firmware (robot):** C++ with the **Arduino ESP32 core**  
  - **Board/SDK:** AI-Thinker ESP32-CAM, `esp32-camera`, `esp_http_server`, `WiFi.h`, **LEDC PWM** for motors, optional **PSRAM**.  
  - **Build:** Arduino IDE 2.x (recommended) or PlatformIO. Custom `partitions.csv`. JSON parsing via **ArduinoJson**.

- **Host-side modules:** **Python 3.10+** (tested 3.11) with one **virtual env per module** (`manual_control/`, `auto_soccer_bot/`, `soccer_vision/`).  
  OS support: Windows, macOS, Linux.

- **Computer-vision & ML stack**
  - **Ultralytics YOLO (v8/v11, PyTorch backend)**  
    - **Used in:** `soccer_vision/` (train/retrain **goal/opponent**); `auto_soccer_bot/` (inference).  
    - **Artifacts:** exported `.pt` weights under `models/`, raw runs under `runs/`, curated plots under `results/`.  
    - **Accel:** CPU by default; optional CUDA build for GPU.
  - **MediaPipe (Hands)**  
    - **Used in:** `manual_control/` for **real-time hand landmarks** → gesture classification (forward/back/left/right/stop).  
    - **Why:** very low latency on CPU; robust to lighting/pose; no GPU required.
  - **OpenCV (cv2)**  
    - **Used in:** frame I/O & decoding, webcam capture, drawing overlays, **HSV** conversions & morphology (color detector), display windows, light pre/post-processing.  
    - **Notes:** keep image ops lightweight to reduce end-to-end latency.
  - **HTTPX (async)**  
    - **Used in:** `auto_soccer_bot/` for **MJPEG intake** from `http://<ESP32_IP>:81/stream` (multipart parsing) and **JSON POST** to `/move`.  
    - **Why:** explicit boundary parsing, backpressure control, and resilient timeouts.
  - **NumPy / standard libs**  
    - **Used in:** array ops, math, `asyncio` loops, simple configs/logging.

- **Models/Artifacts:** **PyTorch `.pt` weights**, Ultralytics run folders (training curves, confusion matrices), curated result images for docs.

- **Annotation & notebooks:** **Label Studio** for dataset labeling (YOLO export). **Jupyter/VS Code** notebooks for training & demos (`soccer_vision/notebooks/`).

- **Configuration & docs:** JSON/YAML for settings; **Markdown** for docs (multilingual under `docs/en|es|fr`). Optional architecture diagrams (Mermaid/PNG).

- **CLI & tooling (nice to have):** `curl` for endpoint tests, `ffplay/VLC` for stream checks, `ipykernel` for pinned notebook kernels.

---

### Python environments (one per host-side module)

To keep dependencies clean and reproducible, the host code uses **three isolated Python environments**—one for each Python-based module:

1. **`auto_soccer_bot/`** — automatic mode (vision + controller)  
2. **`manual_control/`** — gesture teleoperation  
3. **`soccer_vision/`** — training & evaluation for **goal/opponent** detection

Each module ships its own `requirements.txt`. Create and activate the environment **inside the module directory**.