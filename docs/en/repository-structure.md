## Repository structure

The codebase is split into **four top-level modules**, each owning a distinct part of the system. Documentation lives in `docs/` and deeper, per-module guides follow in later sections.

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

- **`opponent-detector/` — Model training & evaluation**
  - Dataset layout (`train/`, `val/`), training script, inference test, and **artifacts** (curves, confusion matrices, saved weights).
  - **Language/Tooling:** Python with the Ultralytics/YOLO stack (see `requirements.txt`).
<br>
> Supporting folders  
> - **`docs/`**: multilingual documentation (`en/`, `es/`, `fr/`).  
> - **`LICENSE` / `README.md`**: licensing and high-level overview.

---

### Languages & tooling

- **Firmware (robot):** C++ with the **Arduino ESP32 core** (sketch in `esp32cam_robot.ino`, supporting C++ sources under `src/`).
- **Host-side modules:** **Python 3.x** for perception, decision, and telemetry.
- **Models/Artifacts:** PyTorch `.pt` weights.
- **Configuration & docs:** JSON/YAML, Markdown.

---

### Python environments (one per host-side module)

To keep dependencies clean and reproducible, the host code uses **three isolated Python environments**—one for each Python-based module:

1. **`auto_soccer_bot/`** — automatic mode (vision + controller)  
2. **`manual_control/`** — gesture teleoperation  
3. **`opponent-detector/`** — training & evaluation

Each module ships its own `requirements.txt`. Create and activate the environment **inside the module directory**.