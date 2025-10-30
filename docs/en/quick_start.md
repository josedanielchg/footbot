# 🚀 Quick start

This page helps you go from zero → running in minutes. It’s organized by sub-project:

---
## Table of Contents

- [1) `esp32cam_robot` — Flash the firmware (Arduino IDE)](#1-esp32cam_robot--flash-the-firmware-arduino-ide)
- [2) `manual_control` — Hand-gesture teleoperation (laptop)](#2-manual_control--hand-gesture-teleoperation-laptop)
- [3) `auto_soccer_bot` — Autonomous ball follower (laptop)](#3-auto_soccer_bot--autonomous-ball-follower-laptop)
- [4) `soccer_vision` — Retrain & test custom YOLO (2 classes)](#4-soccer_vision--retrain--test-custom-yolo-2-classes)
- [Common troubleshooting](#common-troubleshooting)
---

## 1) `esp32cam_robot` — Flash the firmware (Arduino IDE)

### Prerequisites

* **Hardware:** ESP32-CAM (AI-Thinker), **USB-to-Serial (FTDI 3.3 V)**, jumper wires
* **Power:** 5 V to the ESP32-CAM (via **5V** pin); **common GND** shared with FTDI
* **Host:** Arduino IDE **2.x** (recommended)

### A. Install the ESP32 platform

1. Open **Arduino IDE** → **File → Preferences** → *Additional Boards Manager URLs*
2. **Tools → Board → Boards Manager…** → search **“esp32 by Espressif Systems”** → **Install**.

### B. Select the proper board & options

* **Board:** `ESP32 Arduino → AI Thinker ESP32-CAM`
* **Upload Speed:** `115200` (stable default)
* **Flash Mode/Freq/Partition:** leave defaults
* **PSRAM:** `Enabled` (recommended for camera)

### C. Wire the ESP32-CAM for flashing

For more information abour wiring click [here](hardware-power.md)
* To enter bootloader: with IO0 tied to GND, press **RESET** once; keep IO0-GND during upload.

> After upload, **disconnect IO0 from GND** and press **RESET** to run the program.

### D. Open the sketch & configure Wi-Fi / pins

1. In Arduino IDE, open: `esp32cam_robot/esp32cam_robot.ino`
2. Fill in your **Wi-Fi SSID/PASSWORD** and verify any **GPIO / motor driver** definitions (in a `config.h` or at the top of the sketch).
3. **Tools → Port:** select your FTDI COM port (`/dev/ttyUSB*` on Linux, `/dev/cu.*` on macOS, `COM*` on Windows).

### E. Upload & verify

1. Click **Upload**. If you see sync errors, tap **RESET** once (IO0 must be on GND).
2. When upload finishes: remove **IO0–GND**, press **RESET**.
3. Open **Serial Monitor** at **115200** baud. The ESP32-CAM should print its **IP address**.
4. Quick sanity tests (examples):

   * Snapshot: `http://<ESP32_IP>:80/capture`
   * MJPEG stream: `http://<ESP32_IP>:81/stream`
---

## 2) `manual_control` — Hand-gesture teleoperation (laptop)

### Installation

**Prerequisites**

* Python **3.10+** (recommended 3.11)
* A working **webcam**
* The ESP32 robot powered on and reachable on your LAN

**1) Create and activate the environment (`venv_manual_control`)**

> Run these from the **repository root** (parent of `manual_control/`).

**Linux/macOS**

```bash
python3 -m venv manual_control/venv_manual_control
source manual_control/venv_manual_control/bin/activate
```

**Windows (PowerShell)**

```powershell
py -3 -m venv manual_control\venv_manual_control
.\manual_control\venv_manual_control\Scripts\Activate.ps1
```

**2) Install dependencies**

```bash
pip install -r manual_control/requirements.txt
```

**3) Configure endpoints & options**

Edit `manual_control/config.py`:

* Set `ESP32_IP_ADDRESS = "..."` (robot’s IP)
* Optional: adjust `WEBCAM_INDEX`, detection confidences, and speed mapping thresholds.

**4) Run (from the repository root)**

```bash
python -m manual_control.main
```

* An OpenCV window will appear with landmark overlays.
* Press **ESC** to quit.
* Console logs show JSON payloads and HTTP responses.

---

## 3) `auto_soccer_bot` — Autonomous ball follower (laptop)

### Installation

**Prerequisites**

* Python **3.10+** (recommended 3.11)
* ESP32 robot reachable on your LAN and streaming at `http://<ESP32_IP>:81/stream`

**1) Create and activate the environment (`venv_auto_soccer`)**

> Run these from the **repository root** (parent of `auto_soccer_bot/`).

**Linux/macOS**

```bash
python3 -m venv auto_soccer_bot/venv_auto_soccer
source auto_soccer_bot/venv_auto_soccer/bin/activate
```

**Windows (PowerShell)**

```powershell
py -3 -m venv auto_soccer_bot\venv_auto_soccer
.\auto_soccer_bot\venv_auto_soccer\Scripts\Activate.ps1
```

**2) Install dependencies**

```bash
pip install -r auto_soccer_bot/requirements.txt
```

**3) Configure**

Edit `auto_soccer_bot/config_auto.py`:

* Set `ESP32_IP_ADDRESS = "..."` and adjust ports if needed.
* Select **YOLO** weights under `models/` and thresholds.
* Tune controller gains, target corridor, and (optionally) intake resize.

**4) Run (from the repository root)**

```bash
python -m auto_soccer_bot.main
```

* An optional debug window shows detections and steering state.
* Logs print frame timing, chosen command, and HTTP responses.

---

## 4) `soccer_vision` — Retrain & test custom YOLO (2 classes)

This module lets you **(re)train** YOLOv11 to detect **two classes** on-field: `goal` and `opponent`, then **run quick inference** on images/videos. It matches the full guide [here](soccer_vision.md).

### Installation

**Prerequisites**
- Python **3.10+** (3.11 recommended)
- (Optional) CUDA-capable GPU + matching PyTorch build
- (Optional) **Label Studio** for annotation if you’re creating a new dataset

**1) Create & activate a venv (inside the module)**
> Do this **inside** the `soccer_vision/` folder.

**Windows (PowerShell)**
```powershell
cd soccer_vision
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
````

**macOS / Linux**

````bash
cd soccer_vision
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
````

**2) Install dependencies**

````bash
pip install -r requirements.txt
# Optional: pick the right Torch build for your machine
# GPU example (CUDA 12.1):
# pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
# CPU-only:
# pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
````

### Prepare the dataset (Label Studio → YOLO export)

1. Start Label Studio:

   ````bash
   label-studio
   ````
2. At [http://localhost:8080](http://localhost:8080) create a project (e.g., “Soccer Vision”), add **Bounding Box** with labels:

   * `goal`
   * `opponent`
3. Annotate → **Export** as **YOLO (v5/v8/v11)**.
4. Place the export under:

   ````
   soccer_vision/
     dataset/
       train/
         images/
         labels/
       # (optional) val/
       classes.txt   # must contain exactly: goal, opponent
   ````

   *If `val/` is missing, training will create a split from `train/`*

### Train (pick ONE path)

**A) Notebook (recommended for first-time)**

1. Launch Jupyter from the **activated venv**:

   ````bash
   python -m pip install notebook ipykernel  # if missing
   python -m notebook
   ````
2. Open `notebooks/01_retrain_yolo.ipynb` and **Run All**.
   The notebook validates the dataset, creates `data.yaml`, sets `ULTRALYTICS_HOME`, trains, and copies:

   * **Best weights** → `models/yolo11s/soccer_yolo.pt`
   * **Train artifacts** → `models/yolo11s/train_artifacts/`
   * Curated plots can be copied to `results/` for docs.

**B) CLI (headless)**

````bash
# from inside soccer_vision/ (venv active)
python -m notebooks.modules.cli \
  --model yolo11s.pt \
  --epochs 60 \
  --imgsz 640 \
  --batch 16 \
  --train_pct 0.9 \
  --device 0          # GPU 0 (use "cpu" if no GPU)
# Outputs:
#  - models/yolo11s/soccer_yolo.pt
#  - models/yolo11s/train_artifacts/...
#  - runs/ (raw Ultralytics runs)
````

### Quick inference

**Notebook path:** `notebooks/02_test_and_demo.ipynb` (images/videos → saves outputs to `runs/`).

**One-liner (Python)**

````python
from ultralytics import YOLO
m = YOLO("soccer_vision/models/yolo11s/soccer_yolo.pt")
m.predict(
    source="soccer_vision/dataset/val/images",  # or a file/folder/video path
    save=True,
    conf=0.86,                                  # start near F1 peak; tune as needed
    project="soccer_vision/runs",
    name="quick_predict",
    exist_ok=True
)
````

### Where to find results

* **Weights:** `soccer_vision/models/yolo11s/soccer_yolo.pt`
* **Train artifacts (plots, curves, confusion matrix, args):**
  `soccer_vision/models/yolo11s/train_artifacts/`
* **Curated plots for docs:** `soccer_vision/results/`
* **Raw Ultralytics runs:** `soccer_vision/runs/`

> Note: You can find all the results of the trained model at the end of the **Soccer vision** documentation: [here](soccer_vision.md)

### Tips & troubleshooting

* **No `val/` split:** The trainer creates one from `train/` automatically (move by default).
* **GPU not used:** Install the **CUDA-matched** Torch wheel (see commands above) or set `--device cpu`.
* **Confidence threshold:** Start inference around **`conf≈0.86–0.90`** (F1 peak per docs) and adjust for your FP/latency trade-off.
* **Large runs folder:** You can prune old `soccer_vision/runs/` after exporting the best weights.

---

### Common troubleshooting

* **Can’t reach ESP32 IP?** Make sure the ESP32 and laptop are on the **same Wi-Fi** and your router doesn’t isolate clients.
* **Stream stutters?** Keep **QVGA (320×240)** and moderate JPEG quality in firmware; use the **HTTPX** intake modes in the Python apps.
* **Upload fails (ESP32-CAM)?** Re-enter bootloader (IO0→GND + RESET), lower **Upload Speed** to `115200`, check TX/RX crossing, and ensure a **stable 5 V** supply.
* **Permission errors (venv)?** On Windows PowerShell, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
