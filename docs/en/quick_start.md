# 🚀 Quick start

This page helps you go from zero → running in minutes. It’s organized by sub-project:

1. `esp32cam_robot` (flash the firmware on the microcontroller)
2. `manual_control` (hand-gesture teleop from your laptop)
3. `auto_soccer_bot` (autonomous ball follower)
4. `soccer_vision` (TODO)

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

## 4) `soccer_vision` (legacy `opponent-detector`) — *Coming soon*

We’ll add a Jupyter-driven retraining flow (dataset download, split, train, export) and a lightweight inference tester.

> **Placeholder:** setup will mirror the other Python modules (create `venv_soccer_vision`, install `requirements.txt`, run the provided notebook and `test_infer.py`).

---

### Common troubleshooting

* **Can’t reach ESP32 IP?** Make sure the ESP32 and laptop are on the **same Wi-Fi** and your router doesn’t isolate clients.
* **Stream stutters?** Keep **QVGA (320×240)** and moderate JPEG quality in firmware; use the **HTTPX** intake modes in the Python apps.
* **Upload fails (ESP32-CAM)?** Re-enter bootloader (IO0→GND + RESET), lower **Upload Speed** to `115200`, check TX/RX crossing, and ensure a **stable 5 V** supply.
* **Permission errors (venv)?** On Windows PowerShell, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
