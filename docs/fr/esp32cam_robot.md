## Robot ESP32-CAM (`esp32cam_robot/`) — Architecture & fonctionnement

---

## Table des matières

- [Ce que fait ce module](#ce-que-fait-ce-module)
- [Langages & outils de build](#langages--outils-de-build)
- [Structure des dossiers (vue densemble)](#structure-des-dossiers-vue-densemble)
- [Responsabilités des fichiers (résumé)](#responsabilités-des-fichiers-résumé)

---

### Ce que fait ce module
L’ESP32-CAM héberge un **serveur web local** afin que l’ordinateur portable puisse **se connecter en Wi-Fi** pour :
- **Envoyer des commandes de conduite** (avancer/tourner/stop) via HTTP.
- **Récupérer les données caméra** sous forme d’une image JPEG unique (`/capture`) ou d’un **flux MJPEG continu** (`/stream`).

Deux serveurs HTTP sont lancés :
- **Contrôle/Capture** sur le **port 80** → routes : `/`, `/status`, `/control`, `/capture`, `/move`.
- **Streaming** sur le **port 81** → route : `/stream`.

L’ordinateur exécute la perception et la décision ; l’ESP32 se concentre sur la **capteurisation + l’actionnement bas niveau**.

---

### Langages & outils de build
- **Langage :** C++ avec le **core Arduino pour ESP32** (utilise en interne `esp_http_server` d’ESP-IDF).
- **Build :** **Arduino IDE 2.x** (recommandé).  
  - Carte : **AI Thinker ESP32-CAM**.  
  - Activer la **PSRAM** (si disponible).  
  - Ouvrir `esp32cam_robot/esp32cam_robot.ino` et **Téléverser**.

---

### Structure des dossiers (vue d’ensemble)
```

esp32cam_robot/
├─ esp32cam_robot.ino      # Sketch principal (boot, Wi-Fi, caméra, serveurs)
├─ partitions.csv          # Table de partition utilisée par le sketch
└─ src/
├─ handlers/             # Handlers des routes HTTP (caméra + contrôle robot)
├─ vendor/               # En-têtes tiers (ex. ArduinoJson.h)
├─ app_httpd.cpp         # Aides caméra/stream (base exemple ESP32)
├─ camera_index.h        # Page(s) HTML minimale(s) servie(s) sur "/"
├─ camera_pins.h         # Mappage des broches (AI Thinker, etc.)
├─ config.h              # SSID/mot de passe, ports, GPIOs  ⟵ ne pas versionner les secrets
├─ MotorControl.*        # Différentiel (PWM + direction)
├─ CameraController.*    # Init caméra & réglages capteur
├─ LedControl.*          # LED d’état/assistance (si utilisée)
├─ WifiManager.*         # Mise en service Wi-Fi
├─ WebRequestHandlers.*  # Agrège/initialise les handlers d’URI
└─ WebServerManager.*    # Démarre/arrête les deux serveurs HTTP

```

> Les charges utiles des endpoints et la sémantique détaillée de l’API figurent dans la section API. Ci-dessous, une **carte rapide** du rôle principal de chaque fichier.

---

### Responsabilités des fichiers (résumé)

| Chemin | Type | Rôle principal | Interface exposée (fonctions / endpoints) | Notes |
|---|---|---|---|---|
| `esp32cam_robot.ino` | Sketch | Séquence de boot ; init LED & moteurs → caméra → Wi-Fi → démarrage serveurs ; affiche les URLs ; boucle idle | `setup()`, `loop()`, `measure_fps(int)` | Point unique pour changer l’ordre de boot / le logging. |
| `src/config.h` | Config | Configuration à la compilation : modèle caméra, **Wi-Fi SSID/PASS**, ports HTTP, broches moteur/LED | macros : `WIFI_SSID`, `HTTP_CONTROL_PORT`, définitions de broches | Ne pas committer de vraies informations d’identification. |
| `src/CameraController.h` | Pilote | Mise en service et réglage de la caméra ; gestion PSRAM ; taille/qualité initiales | `bool initCamera()`, `sensor_t* getCameraSensor()` | Par défaut JPEG + QVGA pour un streaming fluide. |
| `src/MotorControl.h/.cpp` | Pilote | Conduite différentielle avec **LEDC PWM** ; contrôle de direction | `setupMotors()`, `moveForward/Backward(int)`, `turnLeft/Right(int)`, `arcLeft/Right(int,float)`, `stopMotors()` | Utilise canaux d’activation + broches IN par moteur. |
| `src/WifiManager.h/.cpp` | Réseau | Rejoindre le réseau Wi-Fi, désactiver le sleep, afficher l’IP, gérer le timeout | `bool connectWiFi()` | Retourne `false` en cas d’échec (~20 s). |
| `src/WebServerManager.h/.cpp` | Serveur | Démarrer/arrêter **deux** serveurs HTTP et enregistrer les routes | `bool startWebServer()`, `void stopWebServer()` | Contrôle sur **80** (`/`, `/status`, `/control`, `/capture`, `/move`) ; stream sur **81** (`/stream`). |
| `src/WebRequestHandlers.h/.cpp` | Colle | Agrège/initialise les sous-systèmes de handlers | `initializeWebRequestHandlers()` | Inclut `handlers/camera_handlers.*` et `handlers/robot_control_handlers.*`. |
| `src/handlers/camera_handlers.h/.cpp` | Handlers | Implémentation de l’API web caméra | Endpoints : `"/"` → **index**, `"/status"` → statut JSON, `"/control"` → paramètres caméra (`var`,`val`), `"/capture"` → JPEG, `"/stream"` → MJPEG | Le streaming utilise une frontière multipart ; LED d’assistance optionnelle. |
| `src/handlers/robot_control_handlers.h/.cpp` | Handlers | Exécuter les commandes de mouvement reçues via **HTTP POST JSON** | Endpoint : `"/move"` avec `{direction, speed?, turn_ratio?}` → appelle `MotorControl` | Directions : `forward/backward/left/right/soft_left/soft_right/stop`. |
| `src/app_httpd.cpp` | Support | Utilitaires issus de l’exemple caméra ESP32 (encodage/serving des frames) | helpers internes | Référencé par les handlers caméra. |
| `src/camera_index.h` | UI | HTML gzip pour `/` (variantes spécifiques capteur) | servi par `indexHandler` | Mini page de configuration/statut. |
| `src/camera_pins.h` | Carte HW | Définitions de broches pour cartes ESP32-CAM supportées | macros | Sélection via `CAMERA_MODEL_*` dans `config.h`. |
| `src/LedControl.*` | Pilote | Contrôle LED d’état/assistance (optionnel) | `setupLed()`, `setLedIntensity(int)`, `controlLed(bool,int)`, `setLedStreamingState(bool)` | Utilisé par capture/stream pour signaler l’activité. |
| `src/vendor/ArduinoJson.h` | Tiers | Parsing JSON du corps `/move` | — | En-tête embarqué pour la portabilité. |
| `partitions.csv` | Table de partitions | Table personnalisée (OTA, NVS, coredump, etc.) | — | Nécessaire pour faire tenir caméra + appli OTA. |
| `ci.json` | CI/Matrix build | Presets FQBN Arduino CLI (ESP32/ESP32-S2/S3 ; PSRAM, partitions) | — | Aide à des builds reproductibles en automatisation. |