## 🧪 Project Status

- **Manual Control (gesture teleop)** — ✅ **Working end-to-end.**  
  Runs in real time on a laptop using **OpenCV + MediaPipe**; commands are JSON over HTTP to `/move` with **rate-limiting/debouncing**. Stable on commodity hardware.

- **Automatic Mode (vision-in-the-loop)** — 🟡 **Layers built, not fully integrated.**  
  - **Stream intake:** HTTPX MJPEG reader from `http://<ESP32_IP>:81/stream` — **ready**.  
  - **Perception:**  
    - **Ball** — detector **live** in the loop.  
    - **Goal & Opponent** — models **trained & available** in [`soccer_vision.md`](soccer_vision.md) but **not wired** into the live pipeline.  
  - **Decision:** Tiny **state machine** implements **ball-follower** only (no multi-object fusion yet).  
  - **Actuation:** HTTP POST to `/move` — **ready**.

- **Current limitation** — Autonomy is **single-target (ball)**; features like **shot alignment** and **opponent avoidance** await integration of goal/opponent signals into the controller.

- **Next steps**  
  1) Wire **goal/opponent** detections into the perception bus.  
  2) Extend the state machine with **multi-object fusion** and transitions.  
  3) Tune thresholds/gains and add regression tests for closed-loop behavior.