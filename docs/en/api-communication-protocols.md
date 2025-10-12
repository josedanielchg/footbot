## API & Communication Protocols

### Table of Contents

* [Overview](#overview)
* [Video Streaming Communication](#video-streaming-communication)
* [ESP32 Endpoints](#esp32-endpoints)

  * [Index](#endpoint-index)
  * [Details](#endpoint-details)
  * [cURL examples](#curl-examples)
  * [Project-wide conventions](#project-wide-conventions)
* [Current Security & Validation (Known Limitations)](#current-security--validation-known-limitations)
* [Future Improvements](#future-improvements)
* [Conventions & Defaults](#conventions--defaults)

---

### Overview

* **Roles:**
    - The **ESP32** hosts an **HTTP server** (video + actuator endpoints).
    - The **laptop** is the **HTTP client** (consumer/controller).
* **Transport:** **HTTP over TCP/IP** on the local Wi-Fi.
* **Addressing:** `http://<ESP32_IP>:<PORT>/<path>`

  * Control/Capture server: **port 80**
  * Video streaming server: **port 81**

---

### Video Streaming Communication

* **Purpose:** Low-latency camera feed from ESP32 to laptop.
* **Transport:** **MJPEG over HTTP** (**multipart/x-mixed-replace**).
* **Addressing (actual values):**

  * **Base stream URL:** `http://<ESP32_IP>:81/stream`
  * **MIME:** `Content-Type: multipart/x-mixed-replace;boundary=123456789000000000000987654321`
  * **Boundary token:** `--123456789000000000000987654321`
  * **Headers sent by server:** `X-Timestamp` per frame, `X-Framerate: 60`, `Access-Control-Allow-Origin: *`
* **Behavior:** Client keeps a **long-lived** connection and parses each JPEG part (uses `Content-Length`). Our client uses **HTTPX** to parse parts and always keeps the **latest** decoded frame to minimize lag.

**snapshot endpoint (available):**

* `GET http://<ESP32_IP>:80/capture` → single JPEG (`image/jpeg`), headers include `Content-Disposition` and `X-Timestamp`.

---

### ESP32 Endpoints

Below is the **Endpoint Index** drawn from the firmware:

| Method | Port | Path       | Summary                                            |
| -----: | :--: | ---------- | -------------------------------------------------- |
|    GET |  80  | `/`        | Minimal HTML UI (served per detected sensor model) |
|    GET |  80  | `/control` | Change camera/LED setting via query `var`/`val`    |
|    GET |  80  | `/capture` | Single JPEG snapshot                               |
|   POST |  80  | `/move`    | Robot motion command (JSON)                        |
|    GET |  81  | `/stream`  | MJPEG live video (multipart/x-mixed-replace)       |

#### Endpoint details

**A) `/control` (GET, port 80)**
Adjusts camera/LED settings.

* **Query params:**

  * `?var=<name>&val=<int>`
  * Supported `var` include: `framesize`, `quality`, `contrast`, `brightness`, `saturation`, `gainceiling`, `colorbar`, `awb`, `agc`, `aec`, `hmirror`, `vflip`, `awb_gain`, `agc_gain`, `aec_value`, `aec2`, `dcw`, `bpc`, `wpc`, `raw_gma`, `lenc`, `special_effect`, `wb_mode`, `ae_level`, and (if available) `led_intensity`.
* **Success:** `200` with empty body; **Errors:** `500` on unknown/failed command.
* **CORS:** `Access-Control-Allow-Origin: *`
* **Side effects:** Updates sensor registers / LED PWM.

**B) `/capture` (GET, port 80)**
Single JPEG frame.

* **Response:** `200 image/jpeg`, headers: `Content-Disposition: inline; filename=capture.jpg`, `X-Timestamp`, CORS `*`.
* **Errors:** `500` if capture fails.

**C) `/move` (POST, port 80)**
Motion command for the robot.

* **Request:** `Content-Type: application/json`

  ```json
    {
        "direction": "forward|backward|left|right|soft_left|soft_right|pivot_left|pivot_right|stop",
        "speed": 0-255,
        "turn_ratio": 0.0-1.0 (optional for soft turns)
    }
  ```

  *(In manual mode we typically send just `direction` + `speed`; auto mode include `turn_ratio`.)*
* **Success:** `200 "OK"`
* **Errors:** `400` for empty/malformed JSON or unknown `direction`; `408` on read timeout; `413` if body too large; `500` on internal errors.
* **CORS:** `Access-Control-Allow-Origin: *`
* **Side effects:** Immediately updates motor PWM/directions.

**D) `/stream` (GET, port 81)**
Live MJPEG.

* **MIME:** `multipart/x-mixed-replace; boundary=123456789000000000000987654321`
* **Headers per connection:** `X-Framerate: 60`, CORS `*`
* **Side effects:** LED “streaming” indicator may turn on/off (if wired).

**cURL examples**

```bash
# Capture one frame
curl -o frame.jpg http://<ESP32_IP>:80/capture

# Move forward at speed 150
curl -X POST http://<ESP32_IP>:80/move \
  -H "Content-Type: application/json" \
  -d '{"direction":"forward","speed":150}'
```

**Project-wide conventions**

* **Default Content-Type:** `application/json` for `POST /move`, `image/jpeg` for `/capture`, `multipart/x-mixed-replace` for `/stream`.
* **Status codes:** `200 OK`, `400 Bad Request`, `404 Not Found`, `408 Request Timeout`, `413 Request Entity Too Large`, `500 Internal Server Error`.

---

### Current Security & Validation (Known Limitations)

* **No authentication/authorization:** any LAN client can call endpoints.
* **No transport security:** plain HTTP; traffic is unencrypted.
* **Stateless calls:** no sessions or CSRF protection.
* **Implication:** acceptable for **isolated lab** use; **not** for untrusted networks.

---

### Future Improvements

* **Access control:** pre-shared **API key** header; or **HMAC** (timestamp + nonce); or basic/token auth (resource-permitting).
* **Input validation:** strict schema/range checks for `/control` and `/move`.
* **Rate limiting:** throttle at proxy; backoff strategies in clients.
* **CORS policy:** restrict origins if a browser client is introduced.
* **Observability:** request logging + `/health` endpoint (uptime, heap, FPS).
* **Versioning:** prefix routes with `/v1`; plan for `/v2` changes.

---

### Conventions & Defaults

* **Base URL:** `http://<ESP32_IP>:<PORT>`
* **Client timeouts (laptop):** connect ≈ **2000 ms**, read ≈ **1000 ms** (see Python configs).
* **Units:** speeds `0–255` (8-bit PWM), `turn_ratio 0.0–1.0`, timeouts in ms, frame sizes per sensor enums.

