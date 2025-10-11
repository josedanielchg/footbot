## Manual control (`manual_control/`) — Architecture & Operation

### Index
- [What this module does](#what-this-module-does)
- [Languages & runtime](#languages--runtime)
  - [Core libraries (details)](#core-libraries-details)
- [Folder structure (high level)](#folder-structure-high-level)
- [File responsibilities (summary)](#file-responsibilities-summary)
- [Installation](#installation)
- [Hand commands — gesture → command map](#hand-commands--gesture--command-map)

### What this module does
This host-side module implements **gesture-driven teleoperation**. A laptop webcam provides frames that are processed to detect **hand landmarks** (MediaPipe). The **right** hand encodes **direction** (forward/left/right/backward/stop), and the **left** hand controls **speed** (thumb–index distance). Commands are packaged as JSON and sent over **HTTP** to the ESP32 endpoint `/move`. The loop is asynchronous and **rate-limited** to avoid flooding the robot.

**Pipeline (sense → interpret → command):**
1. **Camera capture** (OpenCV)  
2. **Hand detection & landmarks** (MediaPipe Hands)  
3. **Gesture classification** (direction) + **speed estimation** (left hand)  
4. **Command encoder & transport** (HTTP `POST /move`, JSON)  
5. **Visualization** (overlayed landmarks; ESC to exit)

---

### Languages & runtime
- **Language:** Python 3.10+ (tested with 3.11)
- **Core libraries:** `opencv-python`, `mediapipe`, `httpx`, `asyncio`
- **Network interface:** HTTP (JSON) to ESP32 at `http://<ESP32_IP>:80/move`

#### Core libraries (details)

<p align="center">
  <!-- Add your logos here -->
  <img src="../src/vendor/opencv_logo.jpg" alt="OpenCV logo" height="76" style="margin-right:18px;" />
  <img src="../src/vendor/mediapipe_logo.jpg" alt="MediaPipe logo" height="60" />
</p>

- **OpenCV** — camera capture (`VideoCapture`), RGB↔BGR conversions, window display, on-frame overlays (speed text, etc.).
- **MediaPipe Hands** — real-time **21-landmark** hand tracker used as follows:
  - The input frame is flipped to **selfie view** and converted to **RGB**.
  - `Hands.process()` returns `multi_hand_landmarks` and **handedness** per hand.
  - We extract landmarks for **Right** and **Left** hands.  
    - **Right hand → direction** via `GestureClassifier.classify_gesture()` using finger “up/down” logic based on tip vs. MCP landmarks.  
    - **Left hand → speed** via `GestureClassifier.calculate_speed_from_left_hand()`, mapping the **thumb–index distance** (in pixels, normalized by frame size) to a bounded speed range `[MIN_SPEED, MAX_SPEED]`.
  - Confidence thresholds and max hands are configured in `config.py` (`MIN_DETECTION_CONFIDENCE`, `MIN_TRACKING_CONFIDENCE`, `MAX_NUM_HANDS`).

<p align="center">
  <!-- Hand landmarks guide image placeholder -->
  <img src="../src/vendor/hand-landmarks.png" alt="MediaPipe hand landmarks guide (21 points)" />
</p>

**Figure — Hand landmarks.** We follow the MediaPipe indexing shown above to compute finger states (tip vs. MCP) and the left-hand thumb–index distance used for speed control.

---

### Folder structure (high level)
```

manual_control/
├─ application.py          # Orchestrates the app lifecycle and main loop (async)
├─ camera_manager.py       # Webcam capture wrapper (OpenCV)
├─ config.py               # IP/port, timeouts, gesture/speed thresholds, webcam index
├─ detection_manager_base.py # Abstract base for detectors
├─ gesture_classifier.py   # Gesture → command mapping; left-hand speed estimation
├─ hand_detector.py        # MediaPipe Hands wrapper + drawing utils
├─ main.py                 # Entry point (asyncio.run)
├─ robot_communicator.py   # Async HTTP client with rate limiting/backoff
└─ requirements.txt        # Pinned dependencies

````

> Endpoint and payload details are covered in the API section of the docs. Below we map each file’s **principal purpose**.

---

### File responsibilities (summary)

| Path | Kind | Principal purpose | Key classes / functions | Notes |
|---|---|---|---|---|
| `application.py` | Orchestrator | Initializes camera, detector, comms; runs async control loop; renders overlay | `Application`, `start_application()` | Central glue of the module. |
| `camera_manager.py` | IO | Open/close webcam; read frames safely | `CameraManager.initialize()`, `get_frame()`, `release()` | Uses OpenCV VideoCapture. |
| `config.py` | Config | Network endpoints, timeouts; gesture constants; speed mapping; webcam index | constants | **Set `ESP32_IP_ADDRESS` here.** |
| `detection_manager_base.py` | Abstraction | Interface for pluggable detectors | `DetectionManager` (ABC) | Enables future swap-in detectors. |
| `gesture_classifier.py` | Logic | Right-hand gesture → direction; left-hand distance → speed | `classify_gesture()`, `calculate_speed_from_left_hand()` | Thresholds from `config.py`. |
| `hand_detector.py` | Perception | MediaPipe Hands wrapper; landmark extraction & drawing | `HandDetector.initialize()`, `process_frame()`, `get_detection_data()` | Selfie view (frame flip) enabled. |
| `robot_communicator.py` | Transport | Async HTTP client; dedup & rate-limit command posts | `RobotCommunicator.send_command()` | Posts JSON to `/move`; handles timeouts. |
| `main.py` | Entry | Launches application with `asyncio.run` | — | Run as `python -m manual_control.main`. |
| `requirements.txt` | Dependencies | Pinned runtime deps for reproducibility | — | `opencv-python`, `mediapipe`, `httpx`, `asyncio`. |

---

### Installation

**Prerequisites**
- Python **3.10+** (recommended 3.11)
- A working **webcam**
- The ESP32 robot powered on and reachable on your LAN

**1) Create and activate the environment (`venv_manual_control`)**

> Run these from the **repository root** (parent of `manual_control/`).

**Linux/macOS**
````bash
python3 -m venv manual_control/venv_manual_control
source manual_control/venv_manual_control/bin/activate
````

**Windows (PowerShell)**

````powershell
py -3 -m venv manual_control\venv_manual_control
.\manual_control\venv_manual_control\Scripts\Activate.ps1
````

**2) Install dependencies**

````bash
pip install -r manual_control/requirements.txt
````

**3) Configure endpoints & options**

* Edit `manual_control/config.py`:

  * Set `ESP32_IP_ADDRESS = "..."` (robot’s IP)
  * Optional: adjust `WEBCAM_INDEX`, detection confidences, and speed mapping thresholds.

**4) Run (from the repository root)**

````bash
python -m manual_control.main
````

* An OpenCV window will appear with landmark overlays.
* **ESC** to quit.
* Console logs show JSON payloads and HTTP responses.

---

### Hand commands — gesture → command map

Use the **RIGHT** hand to issue **directional** commands and the **LEFT** hand to modulate **speed** (thumb–index distance). Add the illustrative photos below.

| Command      | Notes                                              |
| ------------ | -------------------------------------------------- |
| **forward**  | All five fingers **down** (curled).                |
| **backward** | Thumb **up**, other four **up**.                   |
| **left**     | Thumb & index **up**, others **down**.             |
| **right**    | Thumb **down**, index–ring **up**, pinky **down**. |
| **stop**     | All five fingers **extended**.                     |

> Speed is computed from the **LEFT** hand’s thumb–index distance and shown in the video overlay.

<img src="../src/picture3.png" alt="MediaPipe logo" />