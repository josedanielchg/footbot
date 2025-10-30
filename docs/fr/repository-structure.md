## Structure du dépôt

Le code est réparti en **quatre modules de haut niveau**, chacun couvrant une partie distincte du système. La documentation se trouve dans `docs/` et des guides détaillés par module suivent dans les sections ultérieures.

---

## Table des matières

- [Modules de haut niveau](#modules-de-haut-niveau)
- [Langages & outillage](#langages--outillage)
- [Environnements Python (un par module côté hôte)](#environnements-python-un-par-module-cote-hote)

---

### Modules de haut niveau

- **`esp32cam_robot/` — Firmware embarqué (sur le robot)**
  - Firmware ESP32-CAM exposant des **endpoints HTTP de contrôle** et du **streaming vidéo**.
  - Sous-systèmes : provisionnement Wi-Fi, serveur web & handlers, pilotes moteur/LED, contrôle caméra.
  - **Langage/Outillage :** C++ (core Arduino pour ESP32), Arduino IDE ou PlatformIO.

- **`manual_control/` — Téléopération par gestes (hôte)**
  - Capture webcam, **détection & classification de la main/gestes**, mappage de commandes, client HTTP vers le robot.
  - **Langage/Outillage :** Python ; voir `requirements.txt` pour les dépendances vision/runtime.
  - Point d’entrée : `main.py`.

- **`auto_soccer_bot/` — Mode automatique (autonomie côté hôte)**
  - Ingestion du flux ESP32-CAM, **détection du ballon**, logique de décision (**suiveur de ballon implémenté**), client HTTP.
  - Fournit des poids YOLO exportés dans `models/` pour des exécutions locales.
  - **Langage/Outillage :** Python ; point d’entrée `main.py`.

- **`soccer_vision/` — Entraînement & évaluation de modèles (YOLOv11, 2 classes : `goal` & `opponent`)**
  - Organisation du jeu de données (`train/`, `val/`), CLI & notebooks d’entraînement, testeur d’inférence rapide, et **artefacts** (courbes, matrices de confusion, poids sauvegardés).
  - **Langage/Outillage :** Python avec la pile Ultralytics/YOLO (voir `requirements.txt`).

<br>

> Dossiers de support
> - **`docs/`** : documentation multilingue (`en/`, `es/`, `fr/`).  
> - **`LICENSE` / `README.md`** : licence et présentation générale.

---

### Langages & outillage (étendu)

- **Firmware (robot) :** C++ avec le **core Arduino pour ESP32**  
  - **Carte/SDK :** AI-Thinker ESP32-CAM, `esp32-camera`, `esp_http_server`, `WiFi.h`, **LEDC PWM** pour moteurs, **PSRAM** optionnelle.  
  - **Build :** Arduino IDE 2.x (recommandé) ou PlatformIO. `partitions.csv` personnalisé. Parsing JSON via **ArduinoJson**.

- **Modules côté hôte :** **Python 3.10+** (testé 3.11) avec **un environnement virtuel par module** (`manual_control/`, `auto_soccer_bot/`, `soccer_vision/`).  
  Systèmes pris en charge : Windows, macOS, Linux.

- **Pile vision & ML**
  - **Ultralytics YOLO (v8/v11, backend PyTorch)**  
    - **Utilisé dans :** `soccer_vision/` (entraîner/réentraîner **goal/opponent**) ; `auto_soccer_bot/` (inférence).  
    - **Artefacts :** poids `.pt` exportés dans `models/`, runs bruts dans `runs/`, graphiques sélectionnés dans `results/`.  
    - **Accélération :** CPU par défaut ; build CUDA optionnelle pour GPU.
  - **MediaPipe (Hands)**  
    - **Utilisé dans :** `manual_control/` pour des **landmarks de main en temps réel** → classification de gestes (forward/back/left/right/stop).  
    - **Pourquoi :** très faible latence sur CPU ; robuste à l’éclairage/pose ; pas de GPU requis.
  - **OpenCV (cv2)**  
    - **Utilisé dans :** E/S & décodage des frames, capture webcam, superpositions, conversions **HSV** & morphologie (détecteur couleur), fenêtres d’affichage, pré/post-traitement léger.  
    - **Notes :** garder les opérations d’image légères pour réduire la latence de bout en bout.
  - **HTTPX (async)**  
    - **Utilisé dans :** `auto_soccer_bot/` pour **l’ingestion MJPEG** depuis `http://<ESP32_IP>:81/stream` (parsing multipart) et **POST JSON** vers `/move`.  
    - **Pourquoi :** parsing explicite du boundary, contrôle du backpressure et timeouts robustes.
  - **NumPy / libs standard**  
    - **Utilisé dans :** opérations sur tableaux, maths, boucles `asyncio`, configs/log.

- **Modèles/Artefacts :** **Poids `.pt` PyTorch**, dossiers de runs Ultralytics (courbes d’entraînement, matrices de confusion), images de résultats sélectionnées pour la doc.

- **Annotation & notebooks :** **Label Studio** pour l’annotation (export YOLO). Notebooks **Jupyter/VS Code** pour entraînement & démos (`soccer_vision/notebooks/`).

- **Configuration & docs :** JSON/YAML pour les paramètres ; **Markdown** pour la doc (multilingue dans `docs/en|es|fr`). Diagrammes d’architecture optionnels (Mermaid/PNG).

- **CLI & outils (bonus) :** `curl` pour tester les endpoints, `ffplay/VLC` pour vérifier le flux, `ipykernel` pour des kernels de notebooks figés.

---

### Environnements Python (un par module côté hôte)

Pour garder des dépendances propres et reproductibles, le code côté hôte utilise **trois environnements Python isolés**—un pour chaque module basé sur Python :

1. **`auto_soccer_bot/`** — mode automatique (vision + contrôleur)  
2. **`manual_control/`** — téléopération par gestes  
3. **`soccer_vision/`** — entraînement & évaluation pour la détection **goal/opponent**

Chaque module fournit son propre `requirements.txt`. Créez et activez l’environnement **dans le répertoire du module**.
