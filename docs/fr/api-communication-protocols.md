### API et Protocoles de Communication
---
#### Table des matières

* [Vue d’ensemble](#overview)
* [Communication du flux vidéo](#video-streaming-communication)
* [Endpoints ESP32](#esp32-endpoints)

  * [Index](#endpoint-index)
  * [Détails](#endpoint-details)
  * [Exemples cURL](#curl-examples)
  * [Conventions globales du projet](#project-wide-conventions)
* [Sécurité & validation actuelles (limitations connues)](#current-security--validation-known-limitations)
* [Améliorations futures](#future-improvements)
* [Conventions & valeurs par défaut](#conventions--defaults)

---

#### Vue d’ensemble

* **Rôles :**

  * L’**ESP32** héberge un **serveur HTTP** (vidéo + endpoints d’actionnement).
  * Le **laptop** est le **client HTTP** (consommateur/contrôleur).
* **Transport :** **HTTP sur TCP/IP** via le Wi-Fi local.
* **Adressage :** `http://<ESP32_IP>:<PORT>/<path>`

  * Serveur de contrôle/capture : **port 80**
  * Serveur de streaming vidéo : **port 81**

---

#### Communication du flux vidéo

* **But :** Flux caméra à faible latence de l’ESP32 vers le laptop.
* **Transport :** **MJPEG sur HTTP** (**multipart/x-mixed-replace**).
* **Adressage (valeurs réelles) :**

  * **URL de base du flux :** `http://<ESP32_IP>:81/stream`
  * **MIME :** `Content-Type: multipart/x-mixed-replace;boundary=123456789000000000000987654321`
  * **Jeton de frontière :** `--123456789000000000000987654321`
  * **En-têtes serveur :** `X-Timestamp` par image, `X-Framerate: 60`, `Access-Control-Allow-Origin: *`
* **Comportement :** Le client maintient une connexion **longue durée** et parse chaque partie JPEG (via `Content-Length`). Notre client **HTTPX** garde toujours **la dernière image décodée** pour réduire la latence.

**Endpoint de capture unique (disponible) :**

* `GET http://<ESP32_IP>:80/capture` → JPEG unique (`image/jpeg`), en-têtes `Content-Disposition` et `X-Timestamp`.

---

#### Endpoints ESP32

**Index des endpoints** tiré du firmware :

| Méthode | Port | Chemin     | Résumé                                            |
| ------: | :--: | ---------- | ------------------------------------------------- |
|     GET |  80  | `/`        | Mini UI HTML (selon le modèle de capteur détecté) |
|     GET |  80  | `/control` | Modifier un réglage caméra/LED via `var`/`val`    |
|     GET |  80  | `/capture` | Capture JPEG unique                               |
|    POST |  80  | `/move`    | Commande de mouvement du robot (JSON)             |
|     GET |  81  | `/stream`  | Vidéo MJPEG en direct (multipart/x-mixed-replace) |

##### Détails des endpoints

**A) `/control` (GET, port 80)**
Ajuste les réglages caméra/LED.

* **Paramètres de requête :**

  * `?var=<name>&val=<int>`
  * `var` pris en charge : `framesize`, `quality`, `contrast`, `brightness`, `saturation`, `gainceiling`, `colorbar`, `awb`, `agc`, `aec`, `hmirror`, `vflip`, `awb_gain`, `agc_gain`, `aec_value`, `aec2`, `dcw`, `bpc`, `wpc`, `raw_gma`, `lenc`, `special_effect`, `wb_mode`, `ae_level` et (si dispo) `led_intensity`.
* **Succès :** `200` sans corps ; **Erreurs :** `500` si commande inconnue/échouée.
* **CORS :** `Access-Control-Allow-Origin: *`
* **Effets :** Met à jour les registres du capteur / PWM du LED.

**B) `/capture` (GET, port 80)**
Image JPEG unique.

* **Réponse :** `200 image/jpeg`, en-têtes : `Content-Disposition: inline; filename=capture.jpg`, `X-Timestamp`, CORS `*`.
* **Erreurs :** `500` en cas d’échec de capture.

**C) `/move` (POST, port 80)**
Commande de déplacement.

* **Requête :** `Content-Type: application/json`

  ```json
  {
    "direction": "forward|backward|left|right|soft_left|soft_right|pivot_left|pivot_right|stop",
    "speed": 0-255,
    "turn_ratio": 0.0-1.0 (optionnel pour les virages doux)
  }
  ```

  *(En mode manuel on envoie généralement `direction` + `speed` ; en mode auto on ajoute `turn_ratio`.)*
* **Succès :** `200 "OK"`
* **Erreurs :** `400` JSON vide/mal formé ou `direction` inconnue ; `408` pour délai de lecture ; `413` si corps trop grand ; `500` pour erreurs internes.
* **CORS :** `Access-Control-Allow-Origin: *`
* **Effets :** Met à jour immédiatement le PWM/la direction des moteurs.

**D) `/stream` (GET, port 81)**
MJPEG en direct.

* **MIME :** `multipart/x-mixed-replace; boundary=123456789000000000000987654321`
* **En-têtes par connexion :** `X-Framerate: 60`, CORS `*`
* **Effets :** Le LED « streaming » peut s’allumer/s’éteindre (si câblé).

**Exemples cURL**

```bash
# Capturer une image
curl -o frame.jpg http://<ESP32_IP>:80/capture

# Avancer à la vitesse 150
curl -X POST http://<ESP32_IP>:80/move \
  -H "Content-Type: application/json" \
  -d '{"direction":"forward","speed":150}'
```

**Conventions globales du projet**

* **Content-Type par défaut :** `application/json` pour `POST /move`, `image/jpeg` pour `/capture`, `multipart/x-mixed-replace` pour `/stream`.
* **Codes d’état :** `200 OK`, `400 Bad Request`, `404 Not Found`, `408 Request Timeout`, `413 Request Entity Too Large`, `500 Internal Server Error`.

---

#### Sécurité & validation actuelles (limitations connues)

* **Pas d’authentification/autorisation :** tout client du LAN peut appeler les endpoints.
* **Pas de sécurité de transport :** HTTP en clair ; trafic non chiffré.
* **Appels sans état :** pas de session ni protection CSRF.
* **Implication :** acceptable en **environnement de labo isolé** ; **à éviter** sur des réseaux non sûrs.

---

#### Améliorations futures

* **Contrôle d’accès :** en-tête avec **clé d’API** ; ou **HMAC** (horodatage + nonce) ; ou Basic/JWT si les ressources le permettent.
* **Validation d’entrée :** contrôles stricts de schéma/plages pour `/control` et `/move`.
* **Limitation de débit :** throttling côté proxy ; *backoff* côté clients.
* **Politique CORS :** restreindre les origines si un client web est utilisé.
* **Observabilité :** journalisation des requêtes + endpoint `/health` (uptime, heap, FPS).
* **Versionnement :** préfixer les routes par `/v1` ; anticiper `/v2`.

---

#### Conventions & valeurs par défaut

* **URL de base :** `http://<ESP32_IP>:<PORT>`
* **Timeouts client (laptop) :** connexion ≈ **2000 ms**, lecture ≈ **1000 ms** (voir configs Python).
* **Unités :** vitesses `0–255` (PWM 8 bits), `turn_ratio 0.0–1.0`, délais en ms, tailles d’image selon les énumérations du capteur.