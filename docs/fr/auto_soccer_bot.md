## Mode automatique (`auto_soccer_bot/`) — Architecture et fonctionnement

### Sommaire
- [Ce que fait ce module](#ce-que-fait-ce-module)
- [Pipeline](#pipeline)
- [Langages & environnement d’exécution](#langages--environnement-dexécution)
  - [Bibliothèques principales (OpenCV · HTTPX · YOLO)](#bibliothèques-principales-opencv--httpx--yolo)
- [Difficultés rencontrées](#difficultés-rencontrées)
- [Structure des dossiers (vue d’ensemble)](#structure-des-dossiers-vue-densemble)
- [Rôles des fichiers (résumé)](#rôles-des-fichiers-résumé)
- [Installation](#installation)

### Ce que fait ce module
Son objectif est de permettre au robot de se gérer **de manière autonome** pour marquer des buts, identifier les adversaires sur le terrain et fonctionner au sein d’un système multi-robots. Chaque robot est autonome : il détecte et suit le ballon, le conduit vers le but et reconnaît les adversaires.

---
### Pipeline

1) **Ingestion du flux (ESP32 → ordinateur portable)**
   - **Protocole :** MJPEG via HTTP à **`http://<ESP32_IP>:81/stream`** (`multipart/x-mixed-replace`).  
   - **Lecteur :** `httpx.AsyncClient.stream("GET", ESP32_STREAM_URL)` **sans délai de lecture** et avec **timeout de connexion** depuis `config_auto` (voir `HTTP_TIMEOUT_CONNECT`).  
   - **Géométrie d’image :** on conserve la taille native du flux (**QVGA 320×240** par défaut côté firmware). Un redimensionnement optionnel est commenté pour échanger détail spatial vs. calcul.

2) **Perception (détection hybride du ballon)**
   - **Pourquoi YOLO + couleur ?**  
     - **YOLO (apprentissage)** est robuste aux variations de forme/éclairage, aux occultations partielles et aux couleurs non idéales, mais plus coûteux par image.  
     - **Couleur HSV (règles)** est **très rapide** et réagit à **chaque image**, mais sensible à l’éclairage et au fond.  
     - La combinaison apporte **réactivité (couleur)** + **robustesse (YOLO)** : YOLO est lancé **toutes les N images**, la couleur couvre l’intervalle.
   - **YOLO (Ultralytics)**
     - Exécution toutes les **`DETECTION_INTERVAL`** images (par défaut **6**).  
     - Ciblage via `TARGET_CLASS_NAMES` (ex. `"sports ball"`) avec seuil `DETECTION_CONFIDENCE_THRESHOLD`.  
     - Mise en cache avec **TTL** court (`yolo_ttl_frames = max(DETECTION_INTERVAL*2, 3)`) pour stabiliser entre passages.
   - **Détection par couleur**
     - **Seuillage HSV** avec `LOWER_BALL_COLOR` / `UPPER_BALL_COLOR` pour isoler le jaune/vert d’une balle de tennis.  
     - **Morphologie légère** (flou + ouverture/fermeture) pour réduire le bruit ; **aire minimale de contour** pour filtrer les petits blobs.  
     - **Boosts optionnels de saturation/luminosité** (`SATURATION`, `BRIGHTNESS`) appliqués en HSV pour améliorer la séparabilité en faible éclairage.
   - **Unification**
     - Les deux détecteurs émettent une représentation commune `(center_x, center_y, area)`.  
     - **Règle de priorité :** utiliser **YOLO** si son résultat en cache est **valide**, sinon **couleur**, sinon **None**.

3) **Décision (automate à états finis)**
   - États : **SEARCHING → BALL_DETECTED → APPROACHING → CAPTURED**.  
   - Le **couloir cible** impose un recentrage horizontal : `[TARGET_ZONE_X_MIN=0.30, TARGET_ZONE_X_MAX=0.70] * frame_width`.  
   - En `APPROACHING_BALL`, la conduite applique des **virages doux** (`turn_ratio = APPROACH_TURN_RATIO`) si le ballon est à gauche/droite du couloir ; sinon **avant**.  
   - Compteurs de confirmation (`BALL_CONFIRMATION_THRESHOLD`) et **délais de grâce** (`MAX_ADJUSTMENT_TIMEOUT_MS`, `BALL_LOST_TIMEOUT_MS`) limitent les oscillations.

4) **Actionnement (ordinateur → ESP32)**
   - `POST` JSON vers **`http://<ESP32_IP>:80/move`** avec :  
     ```json
     {"direction": "...", "speed": <0-255>, "turn_ratio": 0.0-1.0}
     ```  
   - Le communicateur **déduplique** les commandes répétées et applique des **limitations de débit** (`MIN_TIME_BETWEEN_ANY_COMMAND_MS`, `COMMAND_SEND_INTERVAL_MS`) pour éviter de saturer le robot.

> **Taille/qualité d’image :** le firmware diffuse en JPEG **QVGA (320×240)** par défaut (`FRAMESIZE_QVGA`, `set_quality(30)` dans `CameraController.h` sur l’ESP32).

---

### Langages & environnement d’exécution
- **Langage :** Python 3.10+ (testé avec 3.11)
- **E/S réseau :** HTTP — flux `http://<ESP32_IP>:81/stream`, commandes `http://<ESP32_IP>:80/move`

#### Bibliothèques principales (OpenCV · HTTPX · YOLO)

<p align="center">
  <!-- Ajoutez des logos si besoin -->
  <img src="../src/vendor/opencv_logo.jpg" alt="Logo OpenCV" height="76" style="margin-right:18px;" />
  <img src="../src/vendor/httpx_logo.png" alt="Logo HTTPX" height="80" style="margin-right:18px;" />
  <img src="../src/vendor/yolo_logo.jpg" alt="Logo YOLO" height="60" />
</p>

- **OpenCV** — décodage JPEG, overlays de visualisation, pré/post-traitement léger.  
- **HTTPX (async)** — ingestion robuste du flux (MJPEG segmenté) et POST des commandes vers `/move`.  
- **YOLO (Ultralytics)** — détection d’objets ; plusieurs poids fournis (YOLOv8/YOLO11). Utilisé avec le détecteur HSV pour une recherche de ballon résiliente.

---

### Difficultés rencontrées (détaillé)

**1) Latence de streaming → délai décisionnel**  
- **Avant :** la capture d’URL OpenCV ajoutait des buffers internes et des lectures bloquantes MJPEG, rendant les commandes “en retard” (files d’attente).  
- **Correctifs :**  
  - Passage à **HTTPX** avec parsing explicite de frontière et **conservation du dernier frame uniquement** (on jette les anciens).  
  - Firmware en **QVGA** avec qualité JPEG modérée pour réduire coût réseau+décode.  
  - Perception lourde **bridée** en exécutant **YOLO et couleur toutes les `DETECTION_INTERVAL` images** pour éliminer les piles d’images en attente.  
- **Résultat :** contrôle **plus réactif**, moins d’images périmées et suivi plus fluide.

**2) Stabilité du flux (timeouts, backpressure, Wi-Fi)**
- **Avant :** la boucle de capture pouvait se bloquer ou accumuler des données non lues avec le jitter Wi-Fi.  
- **Correctifs :**  
  - Streaming **HTTPX** dans une tâche async dédiée avec **timeout de connexion** et **sans timeout de lecture** pour un flux long.  
  - Parsing robuste des en-têtes (`Content-Length`), resynchronisation sur parties mal formées, trimming borné du buffer.  
- **Résultat :** **meilleure résilience** aux coupures et reprise rapide sans redémarrage.

**3) Robustesse vs. vitesse en perception**  
- **Avant :** YOLO à chaque image coûteux ; la seule couleur fragile sous variations d’éclairage/fond.  
- **Correctifs :**  
  - **Détecteur hybride :** YOLO planifié + **HSV couleur à chaque image** ; boosts **HSV** (`SATURATION=3.5`, `BRIGHTNESS=1`), morphologie, filtre par **aire minimale**.  
  - Sortie unifiée `(cx, cy, area)` pour un contrôleur agnostique à la source.  
- **Résultat :** **détections plus stables** avec **moins de calcul**, tout en gardant la réactivité.

**4) Alignement & oscillations**  
- **Avant :** pivot gauche/droite naïf sur l’erreur x instantanée → jitter et changements d’état au passage du centre.  
- **Correctifs :**  
  - **Automate à états** avec **compteurs de confirmation** (`BALL_CONFIRMATION_THRESHOLD`) et **délais de grâce** (`MAX_ADJUSTMENT_TIMEOUT_MS`, `BALL_LOST_TIMEOUT_MS`).  
  - **Couloir cible** `[TARGET_ZONE_X_MIN, TARGET_ZONE_X_MAX]` et **virages doux** via `APPROACH_TURN_RATIO`.  
- **Résultat :** **moins d’oscillation**, transitions plus maîtrisées, approche plus stable.

<p align="center">
  <img src="../src/realignment-process.png" alt="Processus de réalignement" width="500px" />
</p>

**5) Inondation de commandes vers l’ESP32**  
- **Avant :** commandes identiques répétées gaspillaient bande passante et CPU microcontrôleur.  
- **Correctifs :**  
  - **Déduplication + limitation de débit** dans `RobotCommunicator` avec `MIN_TIME_BETWEEN_ANY_COMMAND_MS` et `COMMAND_SEND_INTERVAL_MS` ; suivi du dernier `{direction, speed, turn_ratio}`.  
- **Résultat :** **moins de bruit** sur le plan de commande et une temporisation plus prévisible.

**6) Portabilité des modèles/artefacts**  
- **Point d’attention :** les poids YOLO sont volumineux et peuvent varier selon les hôtes.  
- **Pratique :** conserver plusieurs poids dans `models/` (ex. `yolov11s.pt` pour CPU) et sélectionner via `config_auto.YOLO_MODEL_PATH`. Utiliser Git LFS ou un store d’artefacts si besoin.

---

### Structure des dossiers (vue d’ensemble)
```

auto_soccer_bot/
├─ application.py              # Orchestration boucle async : ingestion → détection → décision → commande → visu
├─ ball_detector.py            # Détecteur hybride : YOLO (Ultralytics) + HSV en secours
├─ camera_manager.py           # Lecteur MJPEG HTTPX (port 81 /stream) + webcam optionnelle
├─ config_auto.py              # IP/ports, URL de stream, seuils, HSV, gains du contrôleur
├─ detection_manager_base.py   # Interface abstraite des détecteurs
├─ robot_controller.py         # Automate pour suivi et alignement du ballon
├─ robot_communicator.py       # Client HTTP async postant du JSON vers /move (port 80)
├─ main.py                     # Point d’entrée (`python -m auto_soccer_bot.main`)
├─ requirements.txt            # Deps : httpx, opencv-python, ultralytics, numpy, …
└─ models/
    ├─ yolo11l.pt
    ├─ yolo11m.pt
    ├─ yolo11n.pt
    ├─ yolo11s.pt
    └─ yolov8n.pt

````

---

### Rôles des fichiers (résumé)

| Chemin                      | Type          | Rôle principal                                                    | Éléments/Endpoints clés                                                                                                                            | Notes                                                                                                            |
| --------------------------- | ------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `application.py`            | Orchestrateur | Lance les composants ; boucle async ; overlays de debug           | Chaîne : **`CameraManager.get_frame()` → `BallDetector.process_frame()` → `RobotController.decide_action()` → `RobotCommunicator.send_command()`** | Rehaussement couleur via `enhance_frame_colors()` en streaming ; détection planifiée avec `DETECTION_INTERVAL`.  |
| `ball_detector.py`          | Perception    | **Détection hybride** : YOLO toutes N + **HSV** chaque image      | Poids YOLO depuis `config.YOLO_MODEL_PATH` ; cibles `TARGET_CLASS_NAMES` ; HSV `LOWER_BALL_COLOR`/`UPPER_BALL_COLOR`                               | Sortie unifiée `(cx, cy, area)` ; dessine bbox/cercle ; CPU/GPU auto ; cache TTL YOLO.                           |
| `camera_manager.py`         | Ingestion     | Lecteur **HTTPX** MJPEG de l’ESP32                                | **Flux :** `config.ESP32_STREAM_URL` → **`http://<ESP32_IP>:81/stream`** ; boundary `--123456789000000000000987654321`                             | Ne conserve que le **dernier** frame pour réduire la latence ; resize optionnel commenté ; mode webcam supporté. |
| `robot_controller.py`       | Décision      | Automate : **SEARCHING → BALL_DETECTED → APPROACHING → CAPTURED** | Couloir `[TARGET_ZONE_X_MIN, TARGET_ZONE_X_MAX]` ; vitesses `SEARCH_TURN_SPEED`, `APPROACH_SPEED`, `DRIBBLE_SPEED` ; `APPROACH_TURN_RATIO`         | Fenêtres de confirmation et délais de grâce (`BALL_CONFIRMATION_THRESHOLD`, `MAX_ADJUSTMENT_TIMEOUT_MS`).        |
| `robot_communicator.py`     | Transport     | Poste des JSON ; déduplique et limite le débit                    | **Commande :** `config.ESP32_MOVE_ENDPOINT` → **`http://<ESP32_IP>:80/move`** ; payload `{"direction","speed","turn_ratio"}`                       | Garde-fous de débit : `MIN_TIME_BETWEEN_ANY_COMMAND_MS`, `COMMAND_SEND_INTERVAL_MS`.                             |
| `config_auto.py`            | Config        | Paramètres d’exécution                                            | Source `VIDEO_SOURCE` (`esp32_httpx`/`webcam`), boosts HSV, chemin YOLO, gains/seuils                                                              | Par défaut : **QVGA**, `SATURATION=3.5`, `BRIGHTNESS=1`, `DETECTION_INTERVAL=6`.                                 |
| `detection_manager_base.py` | Abstraction   | Interface des détecteurs                                          | `initialize()`, `process_frame()`, `get_detection_data()`                                                                                          | Permet des détecteurs futurs (but/adversaire).                                                                   |
| `main.py`                   | Entrée        | Lancement via `asyncio.run(start_auto_application())`             | —                                                                                                                                                  | Commentaires : **`venv_auto_soccer`** ; conserver la cohérence.                                                  |
| `requirements.txt`          | Deps          | Paquets runtime                                                   | `httpx`, `opencv-python`, `ultralytics`, `numpy`, …                                                                                                | Avec GPU, assurer la compatibilité CUDA/cuDNN.                                                                   |
| `models/*.pt`               | Artefacts     | Poids YOLO                                                        | yolo11*, yolov8n                                                                                                                                   | Modèles légers conseillés sur CPU.                                                                               |

---

### Installation

**Prérequis**

* Python **3.10+** (recommandé 3.11)
* ESP32 joignable sur votre LAN et diffusant `http://<ESP32_IP>:81/stream`

**1) Créer et activer l’environnement (`venv_auto_soccer`)**

> Exécuter depuis la **racine** du dépôt (parent de `auto_soccer_bot/`).

**Linux/macOS**

````bash
python3 -m venv auto_soccer_bot/venv_auto_soccer
source auto_soccer_bot/venv_auto_soccer/bin/activate
````

**Windows (PowerShell)**

````powershell
py -3 -m venv auto_soccer_bot\venv_auto_soccer
.\auto_soccer_bot\venv_auto_soccer\Scripts\Activate.ps1
````

**2) Installer les dépendances**

````bash
pip install -r auto_soccer_bot/requirements.txt
````

**3) Configurer**

* Éditez `auto_soccer_bot/config_auto.py` :

  * Définissez `ESP32_IP_ADDRESS = "..."` et ajustez les ports si nécessaire.
  * Choisissez les poids YOLO dans `models/` et les seuils.
  * Réglez les gains du contrôleur, le couloir cible et (optionnel) le resize à l’ingestion.

**4) Lancer (depuis la racine)**

````bash
python -m auto_soccer_bot.main
````

* Une fenêtre de debug (optionnelle) affichera les détections et l’orientation.
* Les logs montrent le timing des images, la commande choisie et les réponses HTTP.