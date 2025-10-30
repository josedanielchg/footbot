## 🎯 Conclusion, Results & Challenges

### Conclusion
This project demonstrates a complete **sense → interpret → command → act** loop across two modes:
- **Manual Control** — ✅ Fully operational. Real-time, gesture-driven teleoperation from a laptop webcam (MediaPipe + OpenCV) with rate-limited JSON commands to `/move`. See [`manual_control/`](manual_control.md).
- **Automatic Mode** — 🟡 Foundations in place. The pipeline (HTTPX stream intake → hybrid detection → finite-state controller → `/move`) runs with a **ball follower**. **Goal** and **Opponent** detectors are **trained and documented** in [`soccer_vision.md`](soccer_vision.md) but are **not yet integrated** into the live state machine. See [`auto_soccer_bot/`](auto_soccer_bot.md).

### Current Results
- **Manual teleop**: Stable at interactive rates on commodity laptops; smooth overlays and responsive control thanks to **rate-limiting + debouncing**.
- **Autonomy (ball)**: Robust ball tracking via a **hybrid detector** (scheduled YOLO + per-frame HSV) and a **tiny FSM** that centers and advances with soft turns.
- **Streaming**: Low perceived lag after switching to **HTTPX** with “latest-frame only” retention; QVGA MJPEG keeps decode cost low.

### Key Challenges & Mitigations
- **Stream latency / buffering** → Switched to **HTTPX** with explicit multipart parsing and dropped stale frames.
- **Robustness vs. speed in perception** → **YOLO every _N_ frames** + lightweight **HSV** each frame; unified `(cx, cy, area)` output.
- **Command flooding** → **Dedup + rate limits** in the communicator to avoid saturating the ESP32.
- **Controller oscillations** → **Target corridor**, confirmation counters, and grace timeouts in the FSM for steadier alignment.

### What’s Next
1. **Wire goal/opponent signals** from [`soccer_vision`](soccer_vision.md) into the live loop.
2. **Extend the FSM** with **multi-object fusion** (ball + goal + opponent) for shot alignment and obstacle avoidance.
3. **Quantitative eval**: run curated tests (precision/recall, latency budgets) and add regression checks to keep behavior consistent.
