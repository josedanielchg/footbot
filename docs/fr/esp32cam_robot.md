## ESP32-CAM robot (`esp32cam_robot/`) — Architecture & Fonctionnement
---

### Ce que fait ce module
L’ESP32-CAM héberge un **serveur web local** pour que l’ordinateur portable se connecte en **Wi-Fi** et puisse :
- **Envoyer des commandes de déplacement** (avancer, tourner, arrêt) via HTTP.
- **Récupérer des images** en JPEG (`/capture`) ou un **flux MJPEG** continu (`/stream`).

Deux serveurs HTTP sont lancés :
- **Contrôle/Capture** sur le **port 80** → routes : `/`, `/status`, `/control`, `/capture`, `/move`.
- **Streaming** sur le **port 81** → route : `/stream`.

Le portable assure la perception/décision ; l’ESP32 gère le **capteur** et l’**actionnement bas niveau**.

---

### Langages & outils de build
- **Langage :** C++ avec le **noyau Arduino pour ESP32** (utilise `esp_http_server` d’ESP-IDF).
- **Build :** **Arduino IDE 2.x** (recommandé).  
  - Carte : **AI Thinker ESP32-CAM**.  
  - Activer la **PSRAM** (si disponible).  
  - Ouvrir `esp32cam_robot/esp32cam_robot.ino` et **Téléverser**.

---

### Arborescence (haut niveau)
```

esp32cam_robot/
├─ esp32cam_robot.ino      # Sketch principal (boot, Wi-Fi, caméra, serveurs)
├─ partitions.csv          # Table de partitions flash
└─ src/
  ├─ handlers/             # Handlers HTTP (caméra + contrôle robot)
  ├─ vendor/               # En-têtes tiers (ex. ArduinoJson.h)
  ├─ app_httpd.cpp         # Aides caméra/stream (base exemple ESP32)
  ├─ camera_index.h        # Page(s) HTML servies sur "/"
  ├─ camera_pins.h         # Mappage des broches
  ├─ config.h              # SSID/mot de passe, ports, GPIOs  ⟵ ne pas *committer* de secrets
  ├─ MotorControl.*        # Traction différentielle (PWM + direction)
  ├─ CameraController.*    # Initialisation caméra et *tuning*
  ├─ LedControl.*          # LED d’état (si utilisée)
  ├─ WifiManager.*         # Connexion Wi-Fi
  ├─ WebRequestHandlers.*  # Agrégateur/initialiseur de handlers
  └─ WebServerManager.*    # Démarrage/arrêt des deux serveurs HTTP

```

> Les charges utiles et la sémantique détaillée des endpoints figurent dans la section API. Ci-dessous, uniquement le **but principal** de chaque fichier.

---

### Responsabilités des fichiers (résumé)

| Chemin | Type | But principal | Interface exposée (fonctions / endpoints) | Remarques |
|---|---|---|---|---|
| `esp32cam_robot.ino` | Sketch | Séquence de boot ; init LED & moteurs → caméra → Wi-Fi → serveurs ; affiche les URLs ; boucle idle | `setup()`, `loop()`, `measure_fps(int)` | Point central pour l’ordre d’initialisation et les logs. |
| `src/config.h` | Config | Paramètres de compilation : modèle caméra, **SSID/mot de passe**, ports HTTP, broches moteur/LED | macros : `WIFI_SSID`, `HTTP_CONTROL_PORT`, etc. | Éviter de versionner des identifiants réels. |
| `src/CameraController.h` | Pilote | Mise en route et réglage capteur ; gestion PSRAM ; framesize/qualité initiale | `bool initCamera()`, `sensor_t* getCameraSensor()` | Par défaut JPEG + QVGA pour un streaming fluide. |
| `src/MotorControl.h/.cpp` | Pilote | Traction différentielle via **PWM LEDC** ; sens de rotation | `setupMotors()`, `moveForward/Backward(int)`, `turnLeft/Right(int)`, `arcLeft/Right(int,float)`, `stopMotors()` | Utilise canaux *enable* + broches IN par moteur. |
| `src/WifiManager.h/.cpp` | Réseau | Connexion Wi-Fi, désactivation du *sleep*, impression IP, gestion du *timeout* | `bool connectWiFi()` | Retourne `false` après ~20 s si échec. |
| `src/WebServerManager.h/.cpp` | Serveur | Démarrer/arrêter **deux** serveurs HTTP et enregistrer les routes | `bool startWebServer()`, `void stopWebServer()` | Contrôle **80** : `/`, `/status`, `/control`, `/capture`, `/move` · Stream **81** : `/stream`. |
| `src/WebRequestHandlers.h/.cpp` | Colle | Agrège/initialise les sous-systèmes de handlers | `initializeWebRequestHandlers()` | Inclut `handlers/camera_handlers.*` et `handlers/robot_control_handlers.*`. |
| `src/handlers/camera_handlers.h/.cpp` | Handlers | API web de la caméra | Endpoints : `"/"` (index), `"/status"` (JSON), `"/control"` (paramètres), `"/capture"` (JPEG), `"/stream"` (MJPEG) | LED optionnelle pendant capture/stream. |
| `src/handlers/robot_control_handlers.h/.cpp` | Handlers | Exécution des ordres de mouvement via **POST JSON** | Endpoint : `"/move"` avec `{direction, speed?, turn_ratio?}` → `MotorControl` | Directions : `forward/backward/left/right/soft_* / stop`. |
| `src/app_httpd.cpp` | Support | Utilitaires issus de l’exemple caméra ESP32 (encodage/servi des frames) | — | Utilisé par les handlers caméra. |
| `src/camera_index.h` | UI | HTML gzip servi sur `/` (variante selon capteur) | servi par `indexHandler` | Petite page d’état/config. |
| `src/camera_pins.h` | HW | Définition des broches pour cartes supportées | macros | Sélectionné via `CAMERA_MODEL_*` dans `config.h`. |
| `src/LedControl.*` | Pilote | Contrôle de la LED d’état/assistance | `setupLed()`, `setLedIntensity(int)`, `controlLed(bool,int)`, `setLedStreamingState(bool)` | Intégré à capture/stream. |
| `src/vendor/ArduinoJson.h` | Tiers | Parsing JSON du corps `/move` | — | En-tête embarquée pour portabilité. |
| `partitions.csv` | Mémoire | Table de partitions (OTA, NVS, coredump, etc.) | — | Nécessaire pour caméra + OTA. |
| `ci.json` | Build/CI | *Presets* Arduino CLI (ESP32/S2/S3 ; PSRAM, partitions) | — | Pour des builds reproductibles. |

---