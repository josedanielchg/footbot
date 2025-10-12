### API y Protocolos de Comunicación
---
#### Tabla de contenidos

* [Panorama general](#overview)
* [Comunicación de vídeo en streaming](#video-streaming-communication)
* [Endpoints del ESP32](#esp32-endpoints)

  * [Índice](#endpoint-index)
  * [Detalles](#endpoint-details)
  * [Ejemplos cURL](#curl-examples)
  * [Convenciones del proyecto](#project-wide-conventions)
* [Seguridad y validación actuales (limitaciones conocidas)](#current-security--validation-known-limitations)
* [Mejoras futuras](#future-improvements)
* [Convenciones y valores predeterminados](#conventions--defaults)

---

#### Panorama general

* **Roles:**

  * El **ESP32** aloja un **servidor HTTP** (vídeo + endpoints de actuación).
  * El **portátil** actúa como **cliente HTTP** (consumidor/controlador).
* **Transporte:** **HTTP sobre TCP/IP** en la red Wi-Fi local.
* **Direccionamiento:** `http://<ESP32_IP>:<PORT>/<path>`

  * Servidor de control/captura: **puerto 80**
  * Servidor de streaming de vídeo: **puerto 81**

---

#### Comunicación de vídeo en streaming

* **Propósito:** Proporcionar un flujo de cámara de baja latencia del ESP32 al portátil.
* **Transporte:** **MJPEG sobre HTTP** (**multipart/x-mixed-replace**).
* **Dirección (valores reales):**

  * **URL base del stream:** `http://<ESP32_IP>:81/stream`
  * **MIME:** `Content-Type: multipart/x-mixed-replace;boundary=123456789000000000000987654321`
  * **Token de frontera:** `--123456789000000000000987654321`
  * **Cabeceras enviadas por el servidor:** `X-Timestamp` por fotograma, `X-Framerate: 60`, `Access-Control-Allow-Origin: *`
* **Comportamiento:** El cliente mantiene una conexión **de larga duración** y analiza cada parte JPEG (usa `Content-Length`). Nuestro cliente usa **HTTPX** para parsear las partes y conserva siempre el **fotograma más reciente** para minimizar la latencia.

**Endpoint de snapshot (disponible):**

* `GET http://<ESP32_IP>:80/capture` → una sola imagen JPEG (`image/jpeg`), con cabeceras `Content-Disposition` y `X-Timestamp`.

---

#### Endpoints del ESP32

**Índice de endpoints** tomado del firmware:

| Método | Puerto | Ruta       | Resumen                                           |
| -----: | :----: | ---------- | ------------------------------------------------- |
|    GET |   80   | `/`        | UI HTML mínima (según modelo de sensor detectado) |
|    GET |   80   | `/control` | Cambia ajustes de cámara/LED vía `var`/`val`      |
|    GET |   80   | `/capture` | Snapshot JPEG único                               |
|   POST |   80   | `/move`    | Comando de movimiento del robot (JSON)            |
|    GET |   81   | `/stream`  | Vídeo MJPEG en vivo (multipart/x-mixed-replace)   |

##### Detalles de endpoints

**A) `/control` (GET, puerto 80)**
Ajusta parámetros de cámara/LED.

* **Query params:**

  * `?var=<name>&val=<int>`
  * `var` soportados: `framesize`, `quality`, `contrast`, `brightness`, `saturation`, `gainceiling`, `colorbar`, `awb`, `agc`, `aec`, `hmirror`, `vflip`, `awb_gain`, `agc_gain`, `aec_value`, `aec2`, `dcw`, `bpc`, `wpc`, `raw_gma`, `lenc`, `special_effect`, `wb_mode`, `ae_level` y (si está disponible) `led_intensity`.
* **Éxito:** `200` sin cuerpo; **Errores:** `500` si el comando falla o es desconocido.
* **CORS:** `Access-Control-Allow-Origin: *`
* **Efectos secundarios:** Actualiza registros del sensor / PWM del LED.

**B) `/capture` (GET, puerto 80)**
Fotograma JPEG único.

* **Respuesta:** `200 image/jpeg`, cabeceras: `Content-Disposition: inline; filename=capture.jpg`, `X-Timestamp`, CORS `*`.
* **Errores:** `500` si la captura falla.

**C) `/move` (POST, puerto 80)**
Comando de movimiento.

* **Solicitud:** `Content-Type: application/json`

  ```json
  {
    "direction": "forward|backward|left|right|soft_left|soft_right|pivot_left|pivot_right|stop",
    "speed": 0-255,
    "turn_ratio": 0.0-1.0 (opcional para giros suaves)
  }
  ```

  *(En modo manual normalmente enviamos `direction` + `speed`; en modo automático también `turn_ratio`.)*
* **Éxito:** `200 "OK"`
* **Errores:** `400` JSON vacío/mal formado o `direction` desconocido; `408` por timeout de lectura; `413` si el cuerpo es demasiado grande; `500` en errores internos.
* **CORS:** `Access-Control-Allow-Origin: *`
* **Efectos secundarios:** Actualiza inmediatamente PWM/direcciones de los motores.

**D) `/stream` (GET, puerto 81)**
MJPEG en vivo.

* **MIME:** `multipart/x-mixed-replace; boundary=123456789000000000000987654321`
* **Cabeceras por conexión:** `X-Framerate: 60`, CORS `*`
* **Efectos secundarios:** El LED de “streaming” puede encenderse/apagarse (si está cableado).

**Ejemplos cURL**

```bash
# Capturar un fotograma
curl -o frame.jpg http://<ESP32_IP>:80/capture

# Avanzar a velocidad 150
curl -X POST http://<ESP32_IP>:80/move \
  -H "Content-Type: application/json" \
  -d '{"direction":"forward","speed":150}'
```

**Convenciones del proyecto**

* **Content-Type por defecto:** `application/json` para `POST /move`, `image/jpeg` para `/capture`, `multipart/x-mixed-replace` para `/stream`.
* **Códigos de estado:** `200 OK`, `400 Bad Request`, `404 Not Found`, `408 Request Timeout`, `413 Request Entity Too Large`, `500 Internal Server Error`.

---

#### Seguridad y validación actuales (limitaciones conocidas)

* **Sin autenticación/autorización:** cualquier cliente en la LAN puede invocar endpoints.
* **Sin seguridad de transporte:** HTTP en claro; el tráfico no está cifrado.
* **Llamadas sin estado:** no hay sesiones ni protección CSRF.
* **Implicación:** aceptable para **laboratorio aislado**; **no** apto para redes no confiables.

---

#### Mejoras futuras

* **Control de acceso:** cabecera con **API key**; o **HMAC** (timestamp + nonce); o autenticación básica/token si los recursos lo permiten.
* **Validación de entradas:** comprobaciones estrictas de esquema/rangos para `/control` y `/move`.
* **Limitación de tasa:** limitar en proxy; *backoff* en clientes.
* **Política CORS:** restringir orígenes si se usa cliente en navegador.
* **Observabilidad:** *logging* de peticiones + endpoint `/health` (uptime, heap, FPS).
* **Versionado:** prefijar rutas con `/v1`; planificar cambios `/v2`.

---

#### Convenciones y valores predeterminados

* **URL base:** `http://<ESP32_IP>:<PORT>`
* **Timeouts del cliente (portátil):** conexión ≈ **2000 ms**, lectura ≈ **1000 ms** (ver configuración Python).
* **Unidades:** velocidad `0–255` (PWM de 8 bits), `turn_ratio 0.0–1.0`, *timeouts* en ms, tamaños de imagen según *enums* del sensor.